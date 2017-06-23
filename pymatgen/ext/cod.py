# coding: utf-8
# Copyright (c) Pymatgen Development Team.
# Distributed under the terms of the MIT License.

import requests
import subprocess
from monty.dev import requires
from monty.os.path import which

import re
from pymatgen.core.composition import Composition
from pymatgen.core.structure import Structure
from pymatgen.util.string import formula_double_format

"""
This module provides classes to interface with the Crystallography Open 
Database. If you use data from the COD, please cite the following works (as
stipulated by the COD developers)::

    Merkys, A., Vaitkus, A., Butkus, J., Okulič-Kazarinas, M., Kairys, V. & 
    Gražulis, S. (2016) "COD::CIF::Parser: an error-correcting CIF parser for 
    the Perl language". Journal of Applied Crystallography 49. 
    
    Gražulis, S., Merkys, A., Vaitkus, A. & Okulič-Kazarinas, M. (2015) 
    "Computing stoichiometric molecular composition from crystal structures". 
    Journal of Applied Crystallography 48, 85-91.
    
    Gražulis, S., Daškevič, A., Merkys, A., Chateigner, D., Lutterotti, L., 
    Quirós, M., Serebryanaya, N. R., Moeck, P., Downs, R. T. & LeBail, A. 
    (2012) "Crystallography Open Database (COD): an open-access collection of 
    crystal structures and platform for world-wide collaboration". Nucleic 
    Acids Research 40, D420-D427.
    
    Grazulis, S., Chateigner, D., Downs, R. T., Yokochi, A. T., Quiros, M., 
    Lutterotti, L., Manakova, E., Butkus, J., Moeck, P. & Le Bail, A. (2009) 
    "Crystallography Open Database – an open-access collection of crystal 
    structures". J. Appl. Cryst. 42, 726-729.
    
    Downs, R. T. & Hall-Wallace, M. (2003) "The American Mineralogist Crystal
    Structure Database". American Mineralogist 88, 247-250.
"""

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "1.0"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"


class COD(object):
    """
    An interface to the Crystallography Open Database.
    """

    def __init__(self):
        pass

    def query(self, sql):
        r = subprocess.check_output(["mysql", "-u", "cod_reader", "-h",
                                     "www.crystallography.net", "-e",
                                     sql, "cod"])
        return r.decode("utf-8")

    @requires(which("mysql"), "mysql must be installed to use this query.")
    def get_cod_ids(self, formula):
        """
        Queries the COD for all cod ids associated with a formula.

        Args:
            formula (str): Formula.

        Returns:
            List of cod ids.
        """
        # TODO: Remove dependency on external mysql call. MySQL-python package does not support Py3!

        # Standardize formula to the version used by COD.

        sql = 'select file from data where formula="- %s -"' % \
            get_std_formula(formula)
        text = self.query(sql).split("\n")
        cod_ids = []
        for l in text:
            m = re.search("(\d+)", l)
            if m:
                cod_ids.append(int(m.group(1)))
        return cod_ids

    def get_structure_by_id(self, cod_id, **kwargs):
        """
        Queries the COD for a structure by id.

        Args:
            cod_id (int): COD id.
            kwargs: All kwargs supported by Structure.from_str.

        Returns:
            A Structure.
        """
        r = requests.get("http://www.crystallography.net/cod/%s.cif" % cod_id)
        return Structure.from_str(r.text, fmt="cif", **kwargs)

    @requires(which("mysql"), "mysql must be installed to use this query.")
    def get_structure_by_formula(self, formula, **kwargs):
        """
        Queries the COD for structures by formula.

        Args:
            cod_id (int): COD id.
            kwargs: All kwargs supported by Structure.from_str.

        Returns:
            A Structure.
        """
        structures = []
        sql = 'select file, sg from data where formula="- %s -"' % \
              get_std_formula(formula)
        text = self.query(sql).split("\n")
        text.pop(0)
        for l in text:
            if l.strip():
                cod_id, sg = l.split("\t")
                r = requests.get("http://www.crystallography.net/cod/%s.cif"
                                 % cod_id.strip())
                s = Structure.from_str(r.text, fmt="cif", **kwargs)
                structures.append({"structure": s, "cod_id": int(cod_id),
                                   "sg": sg})
        return structures


def get_std_formula(formula):
    c = Composition(formula).element_composition
    values = sorted(c.items(), key=lambda x: x[0].symbol)
    std_formula = ["%s%s" % (k, formula_double_format(v) if v != 1 else "")
                   for k, v in values]
    return " ".join(std_formula)