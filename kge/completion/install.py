#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

def install_completions():
    """Install shell completions for kge."""
    # Get the user's home directory
    home = Path.home()
    
    # Try to find the completion file in the package
    try:
        import kge.completion
        package_dir = Path(kge.completion.__file__).parent
        completion_file = package_dir / "_kge"
        
        if not completion_file.exists():
            raise FileNotFoundError("Completion file not found in package")
    except (ImportError, FileNotFoundError) as e:
        print(f"Error: Could not find completion files in package: {e}")
        print("Please ensure you have installed the latest version of kge-kubectl-get-events")
        sys.exit(1)
    
    # Try to install to system-wide location first
    system_completion_dir = Path("/usr/local/share/zsh/site-functions")
    if system_completion_dir.exists() and os.access(system_completion_dir, os.W_OK):
        try:
            shutil.copy2(completion_file, system_completion_dir)
            print(f"Shell completions installed to {system_completion_dir}")
            print("Please restart your shell to enable completions.")
            return
        except Exception as e:
            print(f"Warning: Could not install to system location: {e}")
            print("Falling back to user installation...")
    
    # Fall back to user installation
    zsh_completion_dir = home / ".zsh" / "completion"
    zsh_completion_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.copy2(completion_file, zsh_completion_dir)
        
        # Add the completion directory to fpath if not already present
        zshrc = home / ".zshrc"
        if zshrc.exists():
            with open(zshrc, 'r') as f:
                content = f.read()
            
            fpath_line = f'fpath=($fpath {zsh_completion_dir})'
            if fpath_line not in content:
                with open(zshrc, 'a') as f:
                    f.write(f'\n# Added by kge\n{fpath_line}\n')
        
        print(f"Shell completions installed to {zsh_completion_dir}")
        print("Please restart your shell or run 'source ~/.zshrc' to enable completions.")
    except Exception as e:
        print(f"Error installing completions: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_completions() 