## [0.1.7] - 2024-10-19
### Changed
- Updated dependencies to include h5netcdf, h5py, pyarrow, and netcdf4

## [0.1.4] - 2024-09-28
### Added
- Simpler method for accessing data using m2m yaml summary file (see 
  notebook 03)
- Added table summarizing the instruments available via m2m (the most 
  commonly requested ones) based on the m2m yaml file. Table accessible via 
  simple import `from yooink import ooi_data_summary` (see notebook 04)

## [0.1.3] - 2024-09-24
### Added
- Incorporate various functionality from the [OOI Data Explorations](https://github.com/oceanobservatories/ooi-data-explorations/tree/master/python) 
  repository. Mainly from common.py.

### Changed
- Refactored to better organize the classes and modules within yooink
- Updated the Jupyter notebook demos to handle these changes and updates.
