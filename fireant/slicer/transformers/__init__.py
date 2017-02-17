# coding: utf-8

from .base import (Transformer,
                   TransformationException)
from .datatables import (DataTablesRowIndexTransformer,
                         DataTablesColumnIndexTransformer)
from .datatables import (DataTablesRowIndexTransformer,
                         DataTablesColumnIndexTransformer,
                         CSVRowIndexTransformer,
                         CSVColumnIndexTransformer)
from .highcharts import (HighchartsLineTransformer,
                         HighchartsAreaTransformer,
                         HighchartsColumnTransformer,
                         HighchartsBarTransformer,
                         HighchartsPieTransformer)
from .notebooks import (PandasRowIndexTransformer,
                        PandasColumnIndexTransformer,
                        MatplotlibLineChartTransformer,
                        MatplotlibBarChartTransformer)

BUNDLES = {
    'notebooks': {
        'row_index_table': PandasRowIndexTransformer(),
        'column_index_table': PandasColumnIndexTransformer(),
        'line_chart': MatplotlibLineChartTransformer(),
        'bar_chart': MatplotlibBarChartTransformer(),
    },
    'highcharts': {
        'line_chart': HighchartsLineTransformer(),
        'area_chart': HighchartsAreaTransformer(),
        'column_chart': HighchartsColumnTransformer(),
        'bar_chart': HighchartsBarTransformer(),
        'pie_chart': HighchartsPieTransformer(),
    },
    'datatables': {
        'row_index_table': DataTablesRowIndexTransformer(),
        'column_index_table': DataTablesColumnIndexTransformer(),
        'row_index_csv': CSVRowIndexTransformer(),
        'column_index_csv': CSVColumnIndexTransformer(),
    },
}
