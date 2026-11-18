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

def black(n, row, column):
    return cell_to_number(n, row, column)

def white(n, row, column):
    return -cell_to_number(n, row, column)

def encode(grid):

    n = len(grid)
    number_variables = n*n # we need that for "p cnf number_variables" "number clauses"

    cnf = []

    # at least 1 of 2 identical numbers in the row shoud be black
    for row in range(n):
        for column1 in range(n):
            for column2 in range(column1 + 1, n):
                if grid[row][column1] == grid[row][column2]:
                    cnf.append([black(n, row, column1), black(n, row, column2)])

    # at least 1 of 2 identical numbers in the column shoud be black
    for column in range(n):
        for row1 in range(n):
                for row2 in range(row1 + 1, n):
                    if grid[row1][column] == grid[row2][column]:
                        cnf.append([black(n, row1, column), black(n, row2, column)])

    #there are no two adjacent black cells
    for row in range(n):
            for column in range(n):
                if column + 1 < n:
                    cnf.append([white(n, row, column), white(n, row, column + 1)])
                if row - 1 < n:
                    cnf.append([white(n, row, column), white(n, row + 1, column)])

    return (cnf, number_variables)
    

               
            
            



