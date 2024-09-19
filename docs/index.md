![Yooink text logo](assets/text-logo.png)

# Yooink Documentation

Welcome! And thanks for checking out the yooink Python package. You can use 
it to access [OOI (Ocean Observatories Initiative)](https://oceanobservatories.org/) 
data, specifically the OOI data that is accessible via the M2M 
(Machine-to-machine) interface. 

There's nothing terribly fancy happening here - yooink essentially provides a 
wrapper around the existing API to make data query and access a bit simpler.
It abstracts away some of the things you may not want to code up manually 
every time - so you can get the data you want more efficiently!

## Installation

You can install this package from [PyPI](https://pypi.org/project/yooink/) using:

```bash
pip install yooink
```

## References

A lot of what's "under the hood", so to speak, is gleaned from either the 
[OOI API cheat sheet](https://ooifb.org/wp-content/uploads/2023/03/API_Cheat_Sheet.pdf)
or from this [Jupyter notebook](https://github.com/ooi-data-review/2018-data-workshops/blob/master/chemistry/examples/quickstart_python.ipynb) 
that walks through an example set-up for accessing data using Python. 

The OOI github organization also hosts [this awesome Python toolset](https://github.com/oceanobservatories/ooi-data-explorations/tree/master/python) if you 
need something more sophisticated, although it does require a bit more work 
to get up and running (you'll need to clone it and run locally in 
development mode).


## Code

You can find the Github repository [here](https://github.com/Waveform-Analytics/yooink).
