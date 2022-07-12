import numpy as np
import pandas as pd

FILE_PATH = './data/table.xlsx'

Eii = {1: 'S11', 2: 'S22', 3: 'M11', 4: 'S33', 5: 'S44', 6: 'M22', 7: 'S55', 8: 'S66', 9: 'M33', 10: 'S77'}


def combination(arr1: list, arr2: list):
    a = len(arr1)
    b = len(arr2)
    if not 0 < a < 4 or not 0 < b < 4:
        print('a and b need to be 1~3.')
        return False

    ret = []
    if a == 1:
        ret.append([[0, 0]])
        ret.append([[0, 1]])
        ret.append([[0, 2]])
    elif a == 2:
        # single-hit
        ret.append([[0, 0]])
        ret.append([[1, 0]])
        # double-hit
        ret.append([[0, 0], [1, 1]])
        ret.append([[0, 1], [1, 0]])
        ret.append([[0, 0], [1, 2]])
        ret.append([[0, 2], [1, 0]])
        ret.append([[0, 1], [1, 2]])
        ret.append([[0, 2], [1, 1]])
    elif a == 3:
        # single-hit
        ret.append([[0, 0]])
        ret.append([[1, 0]])
        ret.append([[2, 0]])
        # double-hit
        ret.append([[0, 0], [1, 1]])
        ret.append([[0, 1], [1, 0]])
        ret.append([[0, 0], [2, 1]])
        ret.append([[0, 1], [2, 0]])
        ret.append([[1, 0], [2, 1]])
        ret.append([[1, 1], [2, 0]])
        # triple-hit
        ret.append([[0, 0], [1, 1], [2, 2]])
        ret.append([[0, 0], [1, 2], [2, 1]])
        ret.append([[0, 1], [1, 0], [2, 2]])
        ret.append([[0, 1], [1, 2], [2, 0]])
        ret.append([[0, 2], [1, 1], [2, 2]])
        ret.append([[0, 2], [1, 2], [2, 1]])

    invalid_indices = []
    for index, val in enumerate(arr2):  # energy == 0 すなわち無効なエネルギーに対するペアを除く
        if val == 0:
            invalid_indices.append(index)

    ret_clean = []
    for pair_list in ret:  # retからinvalid_indicesを含むペアを除去
        pair_list_clean = []
        for pair in pair_list:
            if pair[1] not in invalid_indices:
                pair_list_clean.append(pair)

        if not len(pair_list_clean) == 0:
            ret_clean.append(pair_list_clean)

    return ret_clean


def calc_error(arr1: list, arr2: list, pair_list: list):
    error_ = np.array([])
    for a, b in pair_list:
        error_ = np.append(error_, arr1[a] - arr2[b])
    return {'error': np.linalg.norm(error_), 'pair_list': pair_list}


def find_best_pair(peaks: list, arr: list):
    iterator = combination(peaks, arr)
    errors = {'single-hit': [], 'double-hit': [], 'triple-hit': []}
    for pair_list in iterator:
        if len(pair_list) == 0:
            continue
        elif len(pair_list) == 1:
            errors['single-hit'].append(calc_error(peaks, arr, pair_list))
        elif len(pair_list) == 2:
            errors['double-hit'].append(calc_error(peaks, arr, pair_list))
        elif len(pair_list) == 3:
            errors['triple-hit'].append(calc_error(peaks, arr, pair_list))

    if len(errors) == 0:  # ペアが見つからなかった場合
        print('Not found')
        return 1e10, ()

    best_pair_dict = {}

    for key, value in errors.items():
        if len(value) == 0:
            continue
        sorted_error = sorted(value, key=lambda x: x['error'])
        best_pair_dict[key] = sorted_error[0]

    return best_pair_dict


def calc_diameter(n, m):
    a = 0.246
    a1 = np.array([np.sqrt(3) / 2, 1 / 2]) * a
    a2 = np.array([np.sqrt(3) / 2, - 1 / 2]) * a

    Ch = n * a1 + m * a2
    L = np.linalg.norm(Ch)
    d = L / np.pi
    return d


class Assigner:
    def __init__(self, path='./table.xlsx'):
        self.df = pd.read_excel(path, sheet_name='Sheet1', index_col=0)
        self.df.fillna(0, inplace=True)
        self.peaks = []
        self.assignment_each = {}

        self.Eii = {1: 'S11', 2: 'S22', 3: 'M11', 4: 'S33', 5: 'S44', 6: 'M22', 7: 'S55', 8: 'S66', 9: 'M33', 10: 'S77', 0: 'N/A'}

    def assign(self, peaks: list, mode: str = 'arb'):
        num_peaks = len(peaks)
        if num_peaks < 1 or num_peaks > 3:
            print('Peak list need to contain 1~3 values.')
            return False
        if mode not in ['arb', 'only']:
            print('Mode need to be "arb" or "only".')
            return False

        self.peaks = peaks
        self.assignment_each = {'single-hit': {}, 'double-hit': {}, 'triple-hit': {}}

        for i in range(5, 36):
            df_ex1 = self.df.loc[i]
            for j in range(0, i + 1):
                df_ex2 = df_ex1.iloc[:, j * 2:(j + 1) * 2]
                arr = df_ex2.iloc[:, 1].values.copy()

                best_pair_dict = find_best_pair(peaks, arr)

                if len(best_pair_dict) == 0:
                    continue

                chirality = f'{str(i)}-{str(i - j)}'

                for key in self.assignment_each.keys():
                    best_pair = best_pair_dict.get(key)
                    if best_pair is None:
                        continue
                    self.assignment_each[key][chirality] = best_pair

        for hit_count, assignment in self.assignment_each.items():
            self.assignment_each[hit_count] = sorted(assignment.items(), key=lambda x: x[1]['error'])

    def show_result(self, head=5):
        print(f'search_values: {self.peaks}')
        print("="*50)
        for hit_count, assignment in self.assignment_each.items():
            print()
            print(f'{hit_count}')
            print('-'*50)
            i = 1
            for key, value in assignment:
                if i > head:
                    break
                n, m = map(int, key.split('-'))
                d = calc_diameter(n, m)

                df_ex1 = self.df.loc[n, :]
                df_ex2 = df_ex1.iloc[:, (n - m) * 2:(n - m + 1) * 2]
                print(f'Number {i}')
                print(f'\terror = {value["error"]:.4f}')
                print(f'\t(n, m) = ({n}, {m}), d = {round(d, 2)} nm')
                for j, (row, items) in enumerate(df_ex2.iterrows()):
                    Eii = self.Eii[list(items)[0]]
                    energy = list(items)[1]
                    search_value = ''
                    for pair in value['pair_list']:
                        if j == pair[1]:  # best pairに該当する場合，追記
                            search_value = '<-' + str(self.peaks[pair[0]])
                    print(f'\t{Eii}\t{energy:.2f}\t{search_value}')
                print()
                i += 1

        print("="*50)


def main():
    ac = Assigner()
    while True:
        try:
            peaks = list(map(float, input('ピークエネルギーを入力してください．\n1~3個の値を入力してください．\n例：1.4 1.5 2.1\n>').split()))
            ac.assign(peaks)
            ac.show_result(head=10)
        except ValueError:
            print('終了します．')
            break


if __name__ == '__main__':
    main()