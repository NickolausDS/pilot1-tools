import pandas
import numpy
import tableschema


def get_preview_byte_count(filename, num_rows=11):
    """Count and return number of bytes for the first 11 rows in the given
    filename. Useful for preview."""
    with open(filename) as fp:
        return sum([len(fp.readline()) for x in range(num_rows)])


def get_pandas_field_metadata(pandas_col_metadata, field_name):
    """
    Fetch information for a given column. The column statistics returned
    will be a bit different depending on if the types in the column are a
    number or a string. 'NAN' values are stripped from statistics and don't
    even show up in output.
    """
    pmeta = pandas_col_metadata.get(field_name)
    # Pandas may return numpy.nan for statistics below, or nothing at all.
    # ALL possibly missing values are treated as NAN values and stripped at
    # the end.
    metadata = {
        'name': field_name,
        'type': 'string' if str(pmeta.dtype) == 'object' else str(pmeta.dtype),
        'count': int(pmeta['count']),
        'top': pmeta['top'],

        # string statistics
        'unique': pmeta.get('unique', numpy.nan),
        'frequency': pmeta.get('freq', numpy.nan),

        # numerical statistics
        '25': pmeta.get('25%', numpy.nan),
        '50': pmeta.get('50%', numpy.nan),
        '75': pmeta.get('75%', numpy.nan),
        'mean': pmeta.get('mean', numpy.nan),
        'std': pmeta.get('std', numpy.nan),
        'min': pmeta.get('min', numpy.nan),
        'max': pmeta.get('max', numpy.nan),
    }

    # Remove all NAN values
    cleaned_metadata = {k: v for k, v in metadata.items()
                        if isinstance(v, str) or not numpy.isnan(v)}

    # Pandas has special types for things. Coerce them to be regular
    # ints and floats
    for name in ['25', '50', '75', 'mean', 'std', 'min', 'max']:
        if name in cleaned_metadata:
            cleaned_metadata[name] = float(cleaned_metadata[name])
    for name in ['count', 'unique', 'frequency']:
        if name in cleaned_metadata:
            cleaned_metadata[name] = int(cleaned_metadata[name])
    return cleaned_metadata


def get_foreign_key(foreign_keys, column):
    if not foreign_keys:
        return{'reference': None}
    ref = foreign_keys.get(column['name'], {}).get('reference') or None
    return {'reference': ref}


def analyze_dataframe(filename, foreign_keys=None):
    # Pandas analysis
    df = pandas.read_csv(filename, sep='\t')
    pandas_info = df.describe(include='all')
    # Tableschema analysis
    ts_info = tableschema.Schema(tableschema.infer(filename)).descriptor

    column_metadata = []
    for column in ts_info['fields'][:10]:
        df_metadata = column.copy()
        col_name = column['name']
        df_metadata.update(get_pandas_field_metadata(pandas_info, col_name))
        df_metadata.update(get_foreign_key(foreign_keys, column))
        column_metadata.append(df_metadata)

    dataframe_metadata = {
        'name': 'Data Dictionary',
        # df.shape[0] seems to have issues determining rows
        'numrows': len(df.index),
        'numcols': df.shape[1],
        'previewbytes': get_preview_byte_count(filename),
        'field_definitions': column_metadata,
        'labels': {
            'name': 'Column Name',
            'type': 'Data Type',
            'format': 'Format',
            'count': 'Number of non-null entries',
            '25': '25th Percentile',
            '50': '50th Percentile',
            '75': '75th Percentile',
            'std': 'Standard Deviation',
            'mean': 'Mean Value',
            'min': 'Minimum Value',
            'max': 'Maximum Value',
            'unique': 'Unique Values',
            'top': 'Top Common',
            'frequency': 'Frequency of Top Common Value',
            'reference': 'Link to resource definition'
        }
    }
    return dataframe_metadata
