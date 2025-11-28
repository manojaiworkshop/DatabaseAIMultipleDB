#!/usr/bin/env python3
"""
Download Sentence Transformer Models
Pre-downloads models to avoid download during container startup
"""
import os
import sys
from pathlib import Path

def download_models():
    """Download sentence transformer models to local cache"""
    print("=" * 60)
    print("Downloading Sentence Transformer Models")
    print("=" * 60)
    
    # Set cache directories
    cache_dir = Path("./hf_cache")
    cache_dir.mkdir(exist_ok=True)
    
    os.environ['HF_HOME'] = str(cache_dir.absolute())
    os.environ['TRANSFORMERS_CACHE'] = str(cache_dir / 'transformers')
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(cache_dir / 'sentence_transformers')
    
    try:
        print("\n[1/3] Importing sentence-transformers...")
        from sentence_transformers import SentenceTransformer
        
        print("✓ Import successful\n")
        
        # Model from your config
        model_name = "all-MiniLM-L6-v2"
        
        print(f"[2/3] Downloading model: {model_name}")
        print(f"Cache location: {cache_dir.absolute()}")
        print("This may take a few minutes on first run...")
        print()
        
        # Download and cache the model
        model = SentenceTransformer(model_name)
        
        print(f"\n✓ Model '{model_name}' downloaded successfully!")
        
        # Test encoding
        print("\n[3/3] Testing model encoding...")
        test_sentence = "This is a test sentence"
        embedding = model.encode(test_sentence)
        
        print(f"✓ Test successful! Embedding dimension: {len(embedding)}")
        
        # Show cache size
        cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        cache_size_mb = cache_size / (1024 * 1024)
        
        print("\n" + "=" * 60)
        print(f"✓ All models downloaded successfully!")
        print(f"Cache location: {cache_dir.absolute()}")
        print(f"Cache size: {cache_size_mb:.1f} MB")
        print("=" * 60)
        
        return 0
        
    except ImportError as e:
        print(f"\n✗ Error: Required packages not installed")
        print(f"Details: {e}")
        print("\nPlease install requirements first:")
        print("  pip install sentence-transformers torch")
        return 1
        
    except Exception as e:
        print(f"\n✗ Error downloading models: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(download_models())
