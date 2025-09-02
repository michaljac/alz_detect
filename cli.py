#!/usr/bin/env python3
"""
Alzearly CLI - Command Line Interface for Alzheimer's Prediction Pipeline

Usage:
    python cli.py train --tracker none
    python cli.py train --tracker mlflow --rows 1000
"""

import argparse
import os
import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

def detect_environment() -> Tuple[bool, str]:
    """Detect if Docker is available and determine the best execution method."""
    try:
        # Check if Docker is available
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, "docker"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check if Python dependencies are available
    try:
        import pandas
        import numpy
        import sklearn
        return False, "python"
    except ImportError:
        return False, "none"

def check_dependencies() -> bool:
    """Check if required Python dependencies are installed."""
    required_packages = ['pandas', 'numpy', 'sklearn', 'polars', 'typer']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r requirements-train.txt")
        return False
    
    return True

def setup_paths() -> bool:
    """Setup Python paths and validate project structure."""
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    if not src_path.exists():
        print("❌ src/ directory not found. Are you in the project root?")
        return False
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return True

def import_modules() -> Tuple[bool, dict]:
    """Import required modules with comprehensive error handling."""
    modules = {}
    
    try:
        from src.data_gen import generate
        modules['generate'] = generate
    except ImportError as e:
        print(f"❌ Failed to import data_gen: {e}")
        return False, {}
    
    try:
        from src.preprocess import preprocess
        modules['preprocess'] = preprocess
    except ImportError as e:
        print(f"❌ Failed to import preprocess: {e}")
        return False, {}
    
    try:
        from src.train import train
        modules['train'] = train
    except ImportError as e:
        print(f"❌ Failed to import train: {e}")
        return False, {}
    
    return True, modules

def run_with_docker(args) -> int:
    """Run the pipeline using Docker."""
    try:
        # Build command
        cmd = [
            'docker', 'run', '-it', '--rm',
            '-v', f'{os.getcwd()}:/app',
            '-w', '/app'
        ]
        
        # Add environment variables
        cmd.extend(['alzearly-train', 'python', 'run_training.py'])
        
        # Add arguments
        if args.tracker:
            cmd.extend(['--tracker', args.tracker])
        if args.rows:
            cmd.extend(['--rows', str(args.rows)])
        if args.seed:
            cmd.extend(['--seed', str(args.seed)])
        
        print(f"🚀 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        return result.returncode
        
    except Exception as e:
        print(f"❌ Docker execution failed: {e}")
        return 1

def run_with_python(args, modules) -> int:
    """Run the pipeline using local Python."""
    try:
        print("🧠 Alzearly Training Pipeline")
        print("=" * 50)
        
        # Check for cached data
        featurized_path = Path("/Data/featurized")
        if featurized_path.exists() and any(featurized_path.glob("*")):
            print("✅ Cache hit: Found existing featurized data")
            skip_data_gen = True
            skip_preprocess = True
        else:
            print("📁 No cached data found - will generate new data")
            skip_data_gen = False
            skip_preprocess = False
        
        # Step 1: Data Generation
        if not skip_data_gen:
            print("\n📊 Step 1: Data Generation")
            if args.rows:
                print(f"   Generating {args.rows} rows...")
            modules['generate']()
            print("✅ Data generation completed")
        else:
            print("\n📊 Step 1: Data Generation (skipped - using cached data)")
        
        # Step 2: Preprocessing
        if not skip_preprocess:
            print("\n🔧 Step 2: Data Preprocessing")
            modules['preprocess']()
            print("✅ Data preprocessing completed")
        else:
            print("\n🔧 Step 2: Data Preprocessing (skipped - using cached data)")
        
        # Step 3: Training
        print("\n🤖 Step 3: Model Training")
        print(f"   Tracker: {args.tracker}")
        
        # Set random seed for deterministic runs
        if args.seed:
            from utils import set_seed
            set_seed(args.seed)
        else:
            # Use default seed if not specified
            from utils import set_seed
            set_seed(42)
        
        # Create artifacts directory
        artifacts_dir = Path("artifacts/latest")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Also create timestamped directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_dir = Path(f"artifacts/{timestamp}")
        timestamped_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up experiment tracking based on tracker parameter
        if args.tracker == "mlflow":
            print(f"🔬 Setting up experiment tracking: {args.tracker}")
            from utils import setup_mlflow
            global_tracker, tracker_type = setup_mlflow()
        elif args.tracker == "none":
            print(f"🔬 Setting up experiment tracking: {args.tracker}")
            global_tracker, tracker_type = None, "none"
        else:
            print(f"❌ Invalid tracker option: {args.tracker}")
            return 1
        
        # Set global tracker variables for the training module
        import utils
        utils.tracker = global_tracker
        utils.tracker_type = tracker_type
        
        # Load config and create trainer
        from src.config import load_config
        config = load_config("model", "config/model.yaml")
        
        # Override config if rows specified
        if args.rows:
            # This would need to be handled in data generation
            pass
        
        from src.train import ModelTrainer, TrainingConfig
        trainer_config = TrainingConfig()
        
        # Update random_state in config with the seed from args
        seed_value = args.seed if args.seed else 42
        trainer_config.random_state = seed_value
        trainer_config.xgb_params['random_state'] = seed_value
        trainer_config.lr_params['random_state'] = seed_value
        
        trainer = ModelTrainer(trainer_config)
        
        # Run training
        results = trainer.train(run_type="initial", tracker_type=tracker_type)
        
        print("✅ Model training completed")
        
        # Step 4: Export artifacts
        print("\n📦 Step 4: Exporting Artifacts")
        
        # The training already saved artifacts to artifacts/latest/
        # Just copy them to the timestamped directory
        from src.io.paths import get_latest_artifacts_dir
        
        latest_path = get_latest_artifacts_dir()
        
        # Copy to timestamped directory
        import shutil
        for file in latest_path.glob("*"):
            if file.is_file():
                shutil.copy2(file, timestamped_dir / file.name)
        
        print(f"✅ Artifacts saved to: {latest_path}")
        print(f"✅ Artifacts mirrored to: {timestamped_dir}")
        
        # Print final artifact path
        model_path = latest_path / "model.pkl"
        if model_path.exists():
            print(f"\n🎉 Training completed successfully!")
            print(f"📁 Final model path: {model_path.absolute()}")
            return 0
        else:
            print("❌ Model file not found after training")
            return 1
            
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def train_command(args):
    """Execute the training pipeline."""
    print("🚀 Starting Alzearly Training Pipeline")
    
    # Detect environment
    use_docker, env_type = detect_environment()
    if env_type == "none":
        print("❌ Neither Docker nor Python dependencies available")
        return 1
    
    # Setup paths
    if not setup_paths():
        return 1
    
    # Import modules or use Docker
    if use_docker and not getattr(args, 'force_python', False):
        print("🐳 Using Docker for execution...")
        return run_with_docker(args)
    else:
        print("🐍 Using local Python for execution...")
        if not check_dependencies():
            return 1
        
        import_success, modules = import_modules()
        if not import_success:
            return 1
        
        return run_with_python(args, modules)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Alzearly CLI - Alzheimer's Prediction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py train --tracker none
  python cli.py train --tracker mlflow --rows 1000
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Run the complete training pipeline')
    train_parser.add_argument(
        '--tracker', 
        choices=['none', 'mlflow'], 
        default='none',
        help='Experiment tracker to use (default: none)'
    )
    train_parser.add_argument(
        '--rows', 
        type=int,
        help='Number of rows to generate (for fast testing)'
    )
    train_parser.add_argument(
        '--seed', 
        type=int, 
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    train_parser.add_argument(
        '--force-python',
        action='store_true',
        help='Force local Python execution even if Docker is available'
    )
    
    args = parser.parse_args()
    
    if args.command == 'train':
        return train_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
