## [0.7.0-dev.1](https://github.com/CrackingShells/Hatch/compare/v0.6.2...v0.7.0-dev.1) (2025-09-18)


### Features

* add centralized test data infrastructure for non-TTY testing ([a704937](https://github.com/CrackingShells/Hatch/commit/a70493751e8e74de5b10e79df55088c7a99ad15c))
* add non-TTY handling to dependency installation orchestrator ([ee63d6e](https://github.com/CrackingShells/Hatch/commit/ee63d6eb043fab611100f06ca4fbf0ea89bba711))
* add wobble decorators to test_docker_installer.py ([66740f8](https://github.com/CrackingShells/Hatch/commit/66740f8154e9161c52535c6bea7bbe3b1db40221))
* add wobble decorators to test_env_manip.py ([ec6e0a2](https://github.com/CrackingShells/Hatch/commit/ec6e0a2f17be9c395ab6ef9fac4dfab2d3f317e9))
* add wobble decorators to test_online_package_loader.py ([34b8173](https://github.com/CrackingShells/Hatch/commit/34b8173b9c95768b325e752e9f87785e2785e42d))
* add wobble decorators to test_python_environment_manager.py ([251b0d8](https://github.com/CrackingShells/Hatch/commit/251b0d86fc2a534b1913b2ec1943946082a16f8a))
* add wobble decorators to test_registry_retriever.py ([0bc43fe](https://github.com/CrackingShells/Hatch/commit/0bc43fef091ecae6a55c2c0f5b43f14d86e05132))
* add wobble decorators to test_system_installer.py ([26707b5](https://github.com/CrackingShells/Hatch/commit/26707b574e1712a966d05dd8d8d3300b16d6ec5d))
* complete wobble test categorization ([5a11d45](https://github.com/CrackingShells/Hatch/commit/5a11d451e6e75429483cbc2b8fd996c2bd8349ac))
* implement self-contained test data architecture with 15 core packages ([c7a2fae](https://github.com/CrackingShells/Hatch/commit/c7a2fae40d93ccc9f0c1fd28edb42877541b6781))


### Bug Fixes

* add missing wobble decorators to remaining test files ([e3a1c92](https://github.com/CrackingShells/Hatch/commit/e3a1c928ac3eea81e1a7274252f4ccf63c73559f))
* add required scope parameters to integration test decorators ([ca9cf65](https://github.com/CrackingShells/Hatch/commit/ca9cf65ee683dd78831d81284f235b67f3459347))
* correct wobble integration_test decorator usage ([faf3344](https://github.com/CrackingShells/Hatch/commit/faf3344103845b3e320bee99e386011acd1cce89))
* migrate failing tests to use self-contained test packages ([33c5782](https://github.com/CrackingShells/Hatch/commit/33c578201d4065aba344c27a996523253063667e))
* resolve critical test failures in architecture migration ([c3c3575](https://github.com/CrackingShells/Hatch/commit/c3c3575c3976295355c873b1a02159aa4cb3418e))


### Documentation

* add comprehensive documentation for non-TTY handling ([65c1efb](https://github.com/CrackingShells/Hatch/commit/65c1efb6d0df47f76eb11fe17ff7a091eaec4a4f))
* add mkdocs-print-site-plugin ([#37](https://github.com/CrackingShells/Hatch/issues/37)) ([dd86960](https://github.com/CrackingShells/Hatch/commit/dd869601a81f0cfcef4f905485f2db5572fc43cb))
* enable code copy feature in mkdocs.yml ([300c114](https://github.com/CrackingShells/Hatch/commit/300c114fbc9ad124782dc202ae6e969f50cd635c))
* enable Python requirements installation for documentation build ([#35](https://github.com/CrackingShells/Hatch/issues/35)) ([ea53013](https://github.com/CrackingShells/Hatch/commit/ea530130d3893fdf2e0f4feddcf9606ba797802f))
* enhance documentation with API reference and mkdocstrings integration ([#34](https://github.com/CrackingShells/Hatch/issues/34)) ([b99c964](https://github.com/CrackingShells/Hatch/commit/b99c9642cbb6bca3d2906b476bb92626816d66ef))
* moving from GitHub Pages to Read The Docs ([#32](https://github.com/CrackingShells/Hatch/issues/32)) ([9b7dd07](https://github.com/CrackingShells/Hatch/commit/9b7dd07e9f84637408518c30cfed4f5a79329faa))
* update documentation theme to Material and add mkdocs-material dependency ([#36](https://github.com/CrackingShells/Hatch/issues/36)) ([5fd9a40](https://github.com/CrackingShells/Hatch/commit/5fd9a40897a1a3d8d4930b08bf1496c2ecf3d480))


### Code Refactoring

* eliminate redundant dynamic test package generation ([f497c09](https://github.com/CrackingShells/Hatch/commit/f497c0997e7ae2a3cdf417848f533e42dbf323fd))
* remove sys.path.insert statements from test files ([41c291e](https://github.com/CrackingShells/Hatch/commit/41c291ee9da12d70f1f16a0eebef32cb9bd11444))
