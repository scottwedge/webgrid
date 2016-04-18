from __future__ import absolute_import
from flask import Blueprint, render_template
main = Blueprint('main', __name__)


@main.route('/')
def index():
    from webgrid import NumericColumn
    from webgrid_ta.grids import PeopleGrid as PGBase
    from webgrid_ta.model.entities import Person

    class CurrencyCol(NumericColumn):
        def format_data(self, data):
            return data if int(data) % 2 else data * -1

    class PeopleGrid(PGBase):
        CurrencyCol('Currency', Person.numericcol, format_as='percent', places=5)
        CurrencyCol('C2', Person.numericcol.label('n2'), format_as='accounting')

    pg = PeopleGrid(class_='datagrid')
    pg.apply_qs_args()
    if pg.export_to == 'xls':
        pg.xls.as_response()
    return render_template('index.html', people_grid=pg)
