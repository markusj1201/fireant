from unittest import TestCase
from unittest.mock import (
    ANY,
    Mock,
    patch,
)

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from fireant.slicer.queries.pagination import paginate
from pypika import Order
from ..mocks import (
    cat_uni_dim_df,
    cont_cat_dim_df,
    cont_cat_uni_dim_df,
)

TS = '$d$timestamp'

mock_table_widget = Mock()
mock_table_widget.group_pagination = False

mock_chart_widget = Mock()
mock_chart_widget.group_pagination = True

mock_dimension_definition = Mock()
mock_dimension_definition.alias = '$d$political_party'

mock_metric_definition = Mock()
mock_metric_definition.alias = '$m$votes'


class SimplePaginationTests(TestCase):
    @patch('fireant.slicer.queries.pagination._simple_paginate')
    def test_that_with_no_widgets_using_group_pagination_that_simple_pagination_is_applied(self, mock_paginate):
        paginate(cont_cat_dim_df, [mock_table_widget])

        mock_paginate.assert_called_once_with(ANY, ANY, ANY, ANY)

    @patch('fireant.slicer.queries.pagination._simple_paginate')
    def test_that_with_group_pagination_and_one_dimension_that_simple_pagination_is_applied(self, mock_paginate):
        paginate(cat_uni_dim_df, [mock_table_widget])

        mock_paginate.assert_called_once_with(ANY, ANY, ANY, ANY)

    def test_paginate_with_limit_slice_data_frame_to_limit(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], limit=5)

        expected = cont_cat_dim_df[:5]
        assert_frame_equal(expected, paginated)

    def test_paginate_with_offset_slice_data_frame_from_offset(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], offset=5)

        expected = cont_cat_dim_df[5:]
        assert_frame_equal(expected, paginated)

    def test_paginate_with_limit_and_offset_slice_data_frame_from_offset_to_offset_plus_limit(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], limit=5, offset=5)

        expected = cont_cat_dim_df[5:10]
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_dimension_asc(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], orders=[(mock_dimension_definition, Order.asc)])

        expected = cont_cat_dim_df.sort_values(by=[mock_dimension_definition.alias], ascending=True)
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_dimension_desc(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], orders=[(mock_dimension_definition, Order.desc)])

        expected = cont_cat_dim_df.sort_values(by=[mock_dimension_definition.alias], ascending=False)
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_metric_asc(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], orders=[(mock_metric_definition, Order.asc)])

        expected = cont_cat_dim_df.sort_values(by=[mock_metric_definition.alias], ascending=True)
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_metric_desc(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], orders=[(mock_metric_definition, Order.desc)])

        expected = cont_cat_dim_df.sort_values(by=[mock_metric_definition.alias], ascending=False)
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_multiple_orders(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget], orders=[(mock_dimension_definition, Order.asc),
                                                                           (mock_metric_definition, Order.desc)])

        expected = cont_cat_dim_df.sort_values(by=[mock_dimension_definition.alias, mock_metric_definition.alias],
                                               ascending=[True, False])
        assert_frame_equal(expected, paginated)

    def test_apply_sort_before_slice(self):
        paginated = paginate(cont_cat_dim_df, [mock_table_widget],
                             orders=[(mock_metric_definition, Order.asc)],
                             limit=5, offset=5)

        expected = cont_cat_dim_df.sort_values(by=[mock_metric_definition.alias], ascending=True)[5:10]
        assert_frame_equal(expected, paginated)


class GroupPaginationTests(TestCase):
    @patch('fireant.slicer.queries.pagination._group_paginate')
    def test_with_one_widget_using_group_pagination_that_group_pagination_is_applied(self, mock_paginate):
        paginate(cont_cat_dim_df, [mock_chart_widget, mock_table_widget])

        mock_paginate.assert_called_once_with(ANY, ANY, ANY, ANY)

    def test_paginate_with_limit_slice_data_frame_to_limit_in_each_group(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], limit=2)

        index = cont_cat_dim_df.index
        reindex = pd.MultiIndex.from_product([index.levels[0],
                                              index.levels[1][:2]],
                                             names=index.names)
        expected = cont_cat_dim_df.reindex(reindex) \
            .dropna() \
            .astype(np.int64)
        assert_frame_equal(expected, paginated)

    def test_paginate_with_offset_slice_data_frame_from_offset_in_each_group(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], offset=2)

        index = cont_cat_dim_df.index
        reindex = pd.MultiIndex.from_product([index.levels[0],
                                              index.levels[1][2:]],
                                             names=index.names)
        expected = cont_cat_dim_df.reindex(reindex)
        assert_frame_equal(expected, paginated)

    def test_paginate_with_limit_and_offset_slice_data_frame_from_offset_to_offset_plus_limit_in_each_group(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], limit=1, offset=1)

        index = cont_cat_dim_df.index
        reindex = pd.MultiIndex.from_product([index.levels[0],
                                              index.levels[1][1:2]],
                                             names=index.names)
        expected = cont_cat_dim_df.reindex(reindex) \
            .dropna() \
            .astype(np.int64)
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_dimension_asc(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], orders=[(mock_dimension_definition, Order.asc)])

        expected = cont_cat_dim_df.sort_values(by=[TS, mock_dimension_definition.alias],
                                               ascending=True)
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_dimension_desc(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], orders=[(mock_dimension_definition, Order.desc)])

        expected = cont_cat_dim_df.sort_values(by=[TS, mock_dimension_definition.alias],
                                               ascending=(True, False))
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_metric_asc(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], orders=[(mock_metric_definition, Order.asc)])

        expected = cont_cat_dim_df.iloc[[1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_one_order_metric_desc(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], orders=[(mock_metric_definition, Order.desc)])

        expected = cont_cat_dim_df.iloc[[2, 0, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11]]
        assert_frame_equal(expected, paginated)

    def test_apply_sort_multiple_levels_df(self):
        paginated = paginate(cont_cat_uni_dim_df, [mock_chart_widget], orders=[(mock_metric_definition, Order.asc)])

        sorted_groups = cont_cat_uni_dim_df.groupby(level=[1, 2]).sum().sort_values(by='$m$votes', ascending=True).index
        expected = cont_cat_uni_dim_df \
            .groupby(level=0) \
            .apply(lambda df: df.reset_index(level=0, drop=True).reindex(sorted_groups)) \
            .dropna()
        expected[['$m$votes', '$m$wins']] = expected[['$m$votes', '$m$wins']].astype(np.int64)
        assert_frame_equal(expected, paginated)

    def test_apply_sort_with_multiple_orders(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget], orders=[(mock_dimension_definition, Order.asc),
                                                                           (mock_metric_definition, Order.desc)])

        expected = cont_cat_dim_df.sort_values(by=[TS, mock_dimension_definition.alias, mock_metric_definition.alias],
                                               ascending=[True, True, False])
        assert_frame_equal(expected, paginated)

    def test_apply_sort_before_slice(self):
        paginated = paginate(cont_cat_dim_df, [mock_chart_widget],
                             limit=1, offset=1, orders=[(mock_metric_definition, Order.asc)])

        expected = cont_cat_dim_df.iloc[[0, 3, 5, 7, 9, 11]]
        assert_frame_equal(expected, paginated)
