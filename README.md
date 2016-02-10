# PF2q

PF2q is a tool that works together with FINESSE to reconstruct 2d plasma equilibria. FINESSE, FINite Element Solver for Stationary Equilibria, computes axisymmetric magneto-hydrodynamic equilibria in a coordinate system known as straight field line coordinates, a system in which lines of constant poloidal and toroidal flux appear straight. With PF2q, you can enter an F:=RB_tor and pressure-profile into FINESSE. PF2q will then run FINESSE so multiple parameters, for example the safety factor, pressure and density, are obtained. However, the experimenter might for example be looking for a different safety factor profile than given by FINESSE. Running FINESSE is computationally intensive and the relation between in- and output is sometimes non-intuitive, making it hard to find the right input for the desired output. With PF2q, he/she can change the input profiles, and PF2q will in real-time try to estimate the resulting change in output. When the output is closer to what the experimenter desires, FINESSE can be run again until the FINESSE output matches the desired output.

PF2q was designed for an internship of the Science and Technology of Nuclear Fusion master from the University of Technology Eindhoven at the Dutch Institute For Fundamental Energy Research (DIFFER)

## Install
PF2q is based on Python 2.7, and thus a Python distribution is needed to run. Python is included in most Linux distributions, and can be easily installed on Windows and Mac. For Windows, I prefer to use Anaconda, a scientific Python package. For Mac, I prefer installing Python using a package manager like HomeBrew. PF2q itself does not have to be installed. Just put your script in the parent folder of pf2q like the example_script.py included in this repository.
This repository also includes an example script, which you can edit to run the visual interface of PF2q on your computer. The hardest part is configuring PF2q to be able to run and read out your FINESSE program. For this reason, the easiest way is to adjust the example script with your server/login/path details.

You also need to install the following packages (if you do not have them yet):
- numpy
- scipy
- matplotlib

## Content
- `./pf2q` contains the actual PF2q modules.
  - `finesse.py` and `fem.py` are the hearth of PF2q. They contain functions to run and read FINESSE, as well as the functions use to estimate output and methods to do 1/2d integrals and other FEM procedures.
  - `pf2qvis.py` contains all the methods to draw the GUI of PF2q.
  - `tools.py` and `plot_tools.py` contain some standard convenience functions to calculate and plot various quantities.
  - `asdex.py` contains methods to convert data from the ASDEX tokamak to something `FINESSE/PF2q` can handle. 
  - `unix_functions.py` and `windows_function.py` provide some function prototypes that are able to run and read out FINESSE.
- `./doc` contains a Doxyfile that can be used to generate the documentation found at https://karel-van-de-plassche.github.io/PF2q.
- `./example_files` contain some files that are used by the PF2q example_script.py
- `./final_report` contains the final report for the internship in PDF 
format. It also contains some legacy scripts that were used to generate the pictures in the report. These functions are stored for archival purposes only, as they are outdated and thus do not work with the published PF2q.

## License
This program is licensed under the GPLv3 license, allowing you to freely use, modify and redistribute this code. However, I would appreciate it if you let me know you use my code, for example by following/branching this GitHub repository. I would also appreciate a mention in any publication with results obtained by using my code.
