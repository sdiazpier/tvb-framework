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
Change of DB structure from TVB version 1.3.1 to 1.3.2

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

from sqlalchemy.sql import text
from sqlalchemy import Column, String, Boolean
from migrate.changeset.schema import create_column, drop_column
from tvb.core.entities import model
from tvb.core.entities.storage import SA_SESSIONMAKER


meta = model.Base.metadata
COL_REG1 = Column('_has_surface_mapping', Boolean)
COL_REG2 = Column('_has_volume_mapping', Boolean)
COL_REG3 = Column('_region_mapping', String)
COL_REG4 = Column('_region_mapping_volume', String)
COL_SENSORS = Column('_usable', String)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata.
    """
    meta.bind = migrate_engine
    table1 = meta.tables['MAPPED_TIME_SERIES_DATA']
    table2 = meta.tables['MAPPED_TIME_SERIES_REGION_DATA']
    table3 = meta.tables['MAPPED_SENSORS_DATA']

    create_column(COL_REG1, table1)
    create_column(COL_REG2, table1)
    create_column(COL_REG3, table2)
    create_column(COL_REG4, table2)
    create_column(COL_SENSORS, table3)

    session = SA_SESSIONMAKER()
    session.execute(text("""UPDATE "MAPPED_TIME_SERIES_REGION_DATA" tr SET _region_mapping =
                        (SELECT dt.gid
                         FROM "MAPPED_REGION_MAPPING_DATA" rm, "DATA_TYPES" dt
                         WHERE dt.id = rm.id AND tr._connectivity = rm._connectivity);"""))
    # session.execute(text("""UPDATE "MAPPED_TIME_SERIES_REGION_DATA" tr SET _region_mapping_volume =
    #                     (SELECT dt.gid
    #                      FROM "MAPPED_REGION_VOLUME_MAPPING_DATA" rm, "DATA_TYPES" dt
    #                      WHERE dt.id = rm.id AND tr._connectivity = rm._connectivity);"""))
    session.execute(text("""UPDATE "MAPPED_TIME_SERIES_DATA" ts SET _has_surface_mapping = True
                        WHERE
                            EXISTS (SELECT * FROM "DATA_TYPES" dt
                                    WHERE dt.id=ts.id AND dt.type in ('TimeSeriesSurface', 'TimeSeriesEEG',
                                            'TimeSeriesSEEG', 'TimeSeriesMEG'))
                         OR EXISTS (SELECT * from "MAPPED_TIME_SERIES_REGION_DATA" tr
                                    WHERE tr.id=ts.id AND tr._region_mapping is not NULL);"""))
    session.execute(text("""UPDATE "MAPPED_TIME_SERIES_DATA" ts SET _has_volume_mapping = True
                        WHERE
                            EXISTS (SELECT * FROM "DATA_TYPES" dt
                                    WHERE dt.id=ts.id AND dt.type in ('TimeSeriesVolume'))
                         OR EXISTS (SELECT * from "MAPPED_TIME_SERIES_REGION_DATA" tr
                                    WHERE tr.id=ts.id AND tr._region_mapping_volume is not NULL);"""))

    session.commit()
    session.close()


def downgrade(migrate_engine):
    """
    Operations to reverse the above upgrade go here.
    """
    meta.bind = migrate_engine
    table1 = meta.tables['MAPPED_TIME_SERIES_DATA']
    table2 = meta.tables['MAPPED_TIME_SERIES_REGION_DATA']
    table3 = meta.tables['MAPPED_SENSORS_DATA']

    drop_column(COL_REG1, table1)
    drop_column(COL_REG2, table1)
    drop_column(COL_REG3, table2)
    drop_column(COL_REG4, table2)
    drop_column(COL_SENSORS, table3)
