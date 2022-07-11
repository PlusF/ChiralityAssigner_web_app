from PIL import Image, ImageDraw
import streamlit as st
from ChiralityAssigner import Assigner, calc_diameter

OFFSET = (140, 190)
HEIGHT = (4261 - 190) / 31
WIDTH_list = [150.15, 163.2]
WIDTH_table = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1]


def calc_rect(n: int, m: int):
    if n < m:
        raise ValueError('n must be equal to or greater than m.')

    x1 = OFFSET[0] + sum(WIDTH_list[w] for w in WIDTH_table[:(n - m)])
    y1 = OFFSET[1] + (n - 5) * HEIGHT
    x2 = OFFSET[0] + sum(WIDTH_list[w] for w in WIDTH_table[:(n - m + 1)])
    y2 = y1 + HEIGHT

    return x1, y1, x2, y2


def load_img():
    im = Image.open('app/data/table.png').convert('RGBA')
    return im


def draw_rect(im, n, m, color):
    rect = Image.new('RGBA', im.size)
    dr = ImageDraw.Draw(rect)
    x1, y1, x2, y2 = calc_rect(n, m)
    dr.rectangle((x1, y1, x2, y2), fill=color)
    im = Image.alpha_composite(im, rect)

    return im


def draw_result(im, ca: Assigner, hit_list: list, top: int):
    bool_dict = {'single-hit': hit_list[0], 'double-hit': hit_list[1], 'triple-hit': hit_list[2]}
    color_dict = {'single-hit': [255, 0, 0], 'double-hit': [0, 255, 0], 'triple-hit': [0, 0, 255]}

    msg_all = []

    for hit_count, assignment in ca.assignment_each.items():
        if not bool_dict[hit_count]:
            continue

        msg = f'{hit_count}\n'

        i = 1
        for key, value in assignment:
            if i > top:
                break
            n, m = map(int, key.split('-'))
            d = calc_diameter(n, m)

            color = color_dict[hit_count] + [int(200 - 128 * (i / top))]
            im = draw_rect(im, n, m, tuple(color))

            df_ex1 = ca.df.loc[n, :]
            df_ex2 = df_ex1.iloc[:, (n - m) * 2:(n - m + 1) * 2]

            msg += f'Number {i}\n'
            msg += f'\terror = {value["error"]:.4f}\n'
            msg += f'\t(n, m) = ({n}, {m}), d = {round(d, 2)} nm\n'

            for j, (row, items) in enumerate(df_ex2.iterrows()):
                Eii = ca.Eii[list(items)[0]]
                energy = list(items)[1]
                search_value = ''
                for pair in value['pair_list']:
                    if j == pair[1]:  # best pairに該当する場合，追記
                        search_value = '<-' + str(ca.peaks[pair[0]])
                msg += f'\t{Eii}\t{energy:.2f}\t{search_value}\n\n'

            i += 1

        msg_all.append(msg)

    return im, msg_all


def main():
    ca = Assigner(path='./app/data/table.xlsx')
    st.title('test')

    row1 = st.container()
    col1, col2 = st.columns(2)

    with row1:
        with col1:
            with st.form('form_assign'):
                st.write('Peak energies')
                first_energy = st.text_input('first')
                second_energy = st.text_input('second')
                third_energy = st.text_input('third')
                checkbox_single = st.checkbox('single')
                checkbox_double = st.checkbox('double')
                checkbox_triple = st.checkbox('triple')
                hit_list = [checkbox_single, checkbox_double, checkbox_triple]
                top = st.text_input('Top', '5')

                submitted = st.form_submit_button('Assign')
                if submitted:
                    peaks = []
                    for e in [first_energy, second_energy, third_energy]:
                        try:
                            peaks.append(float(e))
                        except ValueError:
                            print('skipped')
                    ca.assign(peaks)

        with col2:
            st.write('Result')
            im = load_img()
            if submitted:
                im, msg_all = draw_result(im, ca, hit_list, int(top))
            st.image(im, width=1500)

    if submitted:
        row2 = st.container()
        with row2:
            num_cols = sum(hit_list)
            cols = st.columns(num_cols)
            ind = 0
            for i in range(3):
                if not hit_list[i]:
                    continue
                with cols[ind]:
                    st.code(msg_all[ind], language='js')
                ind += 1


if __name__ == '__main__':
    main()
