## Contents
- [Contents](#contents)
- [About](#about)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Citing STREEM](#citing-streem)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## About
The STorage RequirEmEnts and dispatch Model (STREEM) is a high resolution energy model which (i) simulates the operation of renewable energy sources (RES) and electricity storage systems, and (ii) optimises RES and storage capacities. The novelty of STREEM lies in its capability of simulating multiple storage technologies with simple parameterization of its input parameters. That way, it is capable of simulating the simultaneous operation of short-term (e.g., batteries) and long-term storage (e.g., pumped hydro storage), applying priority rules. Furthermore, STREEM can provide economic outputs of examined renewable plus storage configurations, such as the levelized cost of energy of residential PV generation coupled with the appropriate level of storage capacity, or the levelized cost of storage of multiple battery storage technologies. The applicability of STREEM ranges from local energy communities, to national or international scale.

## Quick start
* Install Python 3.9
* Download STREEM from Github and save it in a folder of your preference
* Using a terminal (command line) navigate to the folder where STREEM is saved 
* Type pip install -r requirements.txt
* Type **python streem.py** to run the preconfigured example

## Documentation
Stay tuned for the model documentation

## Citing STREEM
STREEM has been developed as part of the PhD dissertation called [Exploratory assessment of adaptive pathways toward renewable energy systems: a modelling framework facilitating decision making under deep uncertainty](https://www.didaktorika.gr/eadd/handle/10442/56358?locale=en)

In academic literature please cite STREEM as: 
>[![article DOI](https://img.shields.io/badge/article-10.1016/j.enpol.2023.113455-blue)](https://doi.org/10.1016/j.enpol.2023.113455) Michas, S., & Flamos, A. (2023). Are there preferable capacity combinations of renewables and storage? Exploratory quantifications along various technology deployment pathways. Energy Policy, 174, 113455. [https://doi.org/10.1016/j.enpol.2023.113455](https://doi.org/10.1016/j.enpol.2023.113455)


## License
The **STREEM source code** is licensed under the GNU Affero General Public License:

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.



## Acknowledgements
The development of STREEM has been partially supported by the participation of the developer in the:
* EC-funded Horizon 2020 Framework Programme for Research and Innovation (EU H2020) Project titled "Sustainable energy transitions laboratory" (SENTINEL) with grant agreement No. 837089
* EC funded Horizon 2020 Framework Programme for Research and Innovation (EU H2020) Project titled "Enabling Positive Tipping Points towards clean-energy transitions in Coal and Carbon Intensive Regions" (Tipping+) with grant agreement No. 884565
