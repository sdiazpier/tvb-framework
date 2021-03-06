# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
This module is used to measure simulation performance. Some standardized simulations are run and a report is generated.
"""

from time import sleep
from datetime import datetime
from os import path
import tvb_data

if __name__ == "__main__":
    from tvb.basic.profile import TvbProfile
    TvbProfile.set_profile(TvbProfile.COMMAND_PROFILE)

from tvb.core.entities import model
from tvb.core.entities.storage import dao
from tvb.datatypes.connectivity import Connectivity
from tvb.interfaces.command import lab


def _fire_simulation(project_id, **kwargs):
    launched_operation = lab.fire_simulation(project_id, **kwargs)

    # wait for the operation to finish
    while not launched_operation.has_finished:
        sleep(5)
        launched_operation = dao.get_operation_by_id(launched_operation.id)

    if launched_operation.status != model.STATUS_FINISHED:
        raise Exception('simulation failed: ' + launched_operation.additional_info)

    return launched_operation


def _create_bench_project():
    prj = lab.new_project("benchmark_project_ %s" % datetime.now())
    data_dir = path.abspath(path.dirname(tvb_data.__file__))
    zip_path = path.join(data_dir, 'connectivity', 'connectivity_68.zip')
    lab.import_conn_zip(prj.id, zip_path)
    zip_path = path.join(data_dir, 'connectivity', 'connectivity_96.zip')
    lab.import_conn_zip(prj.id, zip_path)
    zip_path = path.join(data_dir, 'connectivity', 'connectivity_192.zip')
    lab.import_conn_zip(prj.id, zip_path)

    conn68 = dao.get_generic_entity(Connectivity, 68, "_number_of_regions")[0]
    conn96 = dao.get_generic_entity(Connectivity, 96, "_number_of_regions")[0]
    conn190 = dao.get_generic_entity(Connectivity, 192, "_number_of_regions")[0]
    return prj, [conn68, conn96, conn190]


HEADER = """
+------------------------+--------+-------+-----------+---------+-----------+
|      Results                                                              |
+------------------------+--------+-------+-----------+---------+-----------+
|        Model           | Sim.   | Nodes |Conduction | time    | Execution |
|                        | Length |       |speed      | step    | time      |
+------------------------+--------+-------+-----------+---------+-----------+
|                        |    (ms)|       |    (mm/ms)|     (ms)| min:sec   |
+========================+========+=======+===========+=========+===========+"""

class Bench(object):
    LINE = HEADER.splitlines()[1]
    COLW = [len(col) - 2 for col in LINE.split('+')[1:-1] ]  # the widths of columns based on the first line of the header
    FS = ' | '.join( '%'+str(cw)+'s' for cw in COLW)  # builds a format string like  "| %6s | %6s | %6s ... "
    FS = '| ' + FS + ' |'

    def __init__(self, model_kws, connectivities, conductions, int_dts, sim_lengths):
        self.model_kws = model_kws
        self.connectivities = connectivities
        self.conductions = conductions
        self.int_dts = int_dts
        self.sim_lengths = sim_lengths
        self.running_times = []

    def run(self, project_id):
        for model_kw in self.model_kws:
            for conn in self.connectivities:
                for length in self.sim_lengths:
                    for dt in self.int_dts:
                        for conduction in self.conductions:
                            launch_args = model_kw.copy()
                            launch_args.update({
                                "connectivity": conn.gid,
                                "simulation_length": str(length),
                                "integrator": "HeunDeterministic",
                                "integrator_parameters_option_HeunDeterministic_dt": str(dt),
                                "conduction_speed": str(conduction),
                            })
                            operation = _fire_simulation(project_id, **launch_args)
                            self.running_times.append( operation.completion_date - operation.start_date )

    def report(self):
        i = 0
        print HEADER
        # use the same iteration order as run_benchmark to interpret running_times
        for model_kw in self.model_kws:
            for conn in self.connectivities:
                for length in self.sim_lengths:
                    for dt in self.int_dts:
                        for conduction in self.conductions:
                            timestr = str(self.running_times[i])[2:-5]
                            print self.FS % (model_kw['model'], length, conn.number_of_regions, conduction, dt, timestr)
                            print self.LINE
                            i += 1


def main():
    """
    Launches a set of standardized simulations and prints a report of their running time.
    Creates a new project for these simulations.
    """
    prj, connectivities = _create_bench_project()

    g2d_epi = Bench(
        model_kws = [
            {"model": "Generic2dOscillator", },
            {"model": "Epileptor", },
        ],
        connectivities= connectivities,
        conductions= [30.0, 3.0],
        int_dts= [0.1, 0.05],
        sim_lengths= [1000],
    )

    larter = Bench(
        model_kws = [
            {"model": "LarterBreakspear", "coupling": "HyperbolicTangent"},
        ],
        connectivities= connectivities,
        conductions = [10.0],
        int_dts = [0.2, 0.1],
        sim_lengths = [10000]
    )

    print 'Generic2dOscillator and Epileptor'
    g2d_epi.run(prj.id)
    g2d_epi.report()

    print 'LarterBreakspear'
    larter.run(prj.id)
    larter.report()


if __name__ == "__main__":
    main()
