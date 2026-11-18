def read_input_to_grid(file):
    with open(file) as f:
        lines = f.read().splitlines()

    grid = []

    for row in lines[1:]:

        row_array = []

        for i in row.split():
            row_array.append(int (i))
        grid.append(row_array)

    return grid

def cell_to_number(n, row, column):
    return n * row + column + 1

