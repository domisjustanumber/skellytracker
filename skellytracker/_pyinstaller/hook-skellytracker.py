"""The PyInstaller hook of skellytracker: data only. A commit that adds a data file type changes `includes`."""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("skellytracker", includes=["**/*.yaml", "**/*.json"], excludes=["**/tests/**"])
hiddenimports = []
