import pandas as pd
from fastai.tabular.all import *
from sklearn.preprocessing import StandardScaler, Normalizer
from category_encoders import OneHotEncoder


def split_data_sets_for_svm(df, temporal_resolution, test_size=0.2, validation_size=0.2):
    data, target, cont_vars, cat_vars = _preprocess_data_for_svm(df=df, temporal_resolution=temporal_resolution)

#    scaler = StandardScaler()
#    scal_data = scaler.fit_transform(X=data[cont_vars])
#    scal_data = pd.DataFrame(scal_data)
#    data = data.drop(columns=cont_vars)
#    data = data.join(scal_data)

    enc = OneHotEncoder(use_cat_names=True, return_df=True, cols=cat_vars)
    enc_data = enc.fit_transform(data[cat_vars])
    enc_data = enc_data.astype("category")
    data = data.join(enc_data)
    data = data.drop(columns=cat_vars)

#    normalizer = Normalizer()
#    norm_data = normalizer.fit_transform(X=data[cont_vars])
#    norm_data = pd.DataFrame(norm_data)
#    data = data.drop(columns=cont_vars)
#    data = data.join(norm_data)

    train_index = int(len(data) * (1 - test_size))
    df_train = data[0:train_index]
    df_test = data[train_index:]

    # Setting indices for creating a validation set
    start_index = len(df_train) - int(len(df_train) * validation_size)
    end_index = len(df_train)
    df_val = df_train[start_index:end_index]
    df_train = df_train[0:start_index]

    # Scale train data
    scaler = StandardScaler()
    scal_data = scaler.fit_transform(X=df_train[cont_vars])
    scal_data = pd.DataFrame(scal_data)
    df_train = df_train.drop(columns=cont_vars)
    df_train = df_train.join(scal_data)

    # Scale validation data
    scaler = StandardScaler()
    scal_data = scaler.fit_transform(X=df_val[cont_vars])
    scal_data = pd.DataFrame(scal_data)
    df_val = df_val.drop(columns=cont_vars)
    df_val = df_val.join(scal_data)

    # Scale test data
    scaler = StandardScaler()
    scal_data = scaler.fit_transform(X=df_test[cont_vars])
    scal_data = pd.DataFrame(scal_data)
    df_test = df_test.drop(columns=cont_vars)
    df_test = df_test.join(scal_data)

    return df_train, df_val, df_test


def _preprocess_data_for_svm(df, temporal_resolution):
    if temporal_resolution == 'D':
        df = add_datepart(df, 'Trip Start Timestamp', prefix='')
    else:
        df = add_datepart(df, 'Trip Start Timestamp', prefix='', time=True)
        _ = [c for c in df.columns if ('minute' in c.lower() or 'second' in c.lower())]
        df.drop(_, axis=1, inplace=True)
    df = df.astype({'Week': 'uint32'})
    df = df.astype({'Elapsed': 'int64'})
    # Only Columns with more than 35 distinct values will be considered as continuous
    target = f"Demand ({temporal_resolution})"
    cont_vars, cat_vars = cont_cat_split(df, max_card=35, dep_var=target)
    # Spacial temporal columns that should be considered as categories in an embedding structure
    cont_vars.remove('Dayofyear')
    cat_vars.append('Dayofyear')
    cont_vars.remove('Week')
    cat_vars.append('Week')
    hex_regex = re.compile(".*hex")
    _ = list(filter(hex_regex.match, cont_vars))
    if bool(_):
        [cont_vars.remove(entry) for entry in _]
        cat_vars.extend(_)
    return df, target, cont_vars, cat_vars
