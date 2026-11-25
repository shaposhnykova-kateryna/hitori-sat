import subprocess
from argparse import ArgumentParser


def read_input_to_grid(input_file_name):
    with open(input_file_name) as f:
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
                if row + 1 < n:
                    cnf.append([white(n, row, column), white(n, row + 1, column)])

    return (cnf, number_variables)

def call_solver(cnf, number_variables, output_name, solver_name, verbosity):

    with open(output_name, "w") as f:
        f.write("p cnf " + str(number_variables) + " " + str(len(cnf)) +'\n')
        for clause in cnf:
            f.write(' '.join(str(literal) for literal in clause) + " " + '0' + '\n')

    return subprocess.run([solver_name, '-model', '-verb=' + str(verbosity) , output_name], stdout=subprocess.PIPE)

def glucose_result_to_model(result):
    if (result.returncode == 20):
        return None

    model = []

    for line in result.stdout.decode('utf-8').split('\n'):
        if line.startswith("v"):  
            variables = line.split(" ")
            variables.remove("v")
            model.extend(int(v) for v in variables)      
    model.remove(0) 
    return model
 
def model_to_black_cells(model, n):

    black_cells = set()

    for row in range(n):
        for column in range(n):
            if  model[cell_to_number(n, row, column) - 1] > 0:
                black_cells.add((row, column))

    return black_cells

# if this function returns 1 component - white cells connected, if more then there are several 'islands' and whitr cells are not connected
def find_white_components(n, black_cells):

    white_cells = set()

    for row in range(n):
        for column in range(n):
            if (row, column) not in black_cells:
                white_cells.add((row, column))

    components = []
    visited = set()

    for start in white_cells:
        if start in visited:
            continue

        component = {start}
        queue = [start]
        visited.add(start)

        while queue:
            row, column = queue.pop()

            for neighbor in neighbors(n, row, column):
                if neighbor in white_cells and neighbor not in visited:
                    visited.add(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)

        components.append(component)

    return components

def neighbors(n, row, column):

    result = []

    if row + 1 < n:
        result.append((row + 1, column))
    if column + 1 < n:
        result.append((row, column + 1))
    if row - 1 >= 0:
        result.append((row - 1, column))
    if column - 1 >= 0:
        result.append((row, column - 1))

    return result



def print_result(grid, black_cells):

    n = len(grid)

    print()
    print("##################################################################")
    print("##################[ Solution of Hitori problem ]#################")
    print("##################################################################")
    print()

    if black_cells is None:
        print("This grid has no solution")
        return

    for row in range(n):
        for column in range(n):
            if (row, column) in black_cells:
                print("■", end=" ")
            else:
                print(grid[row][column], end=" ")
        print()

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        default="input.in",
        type=str,
        help=(
            "The instance file."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="formula.cnf",
        type=str,
        help=(
            "Output file for the DIMACS format (i.e. the CNF formula)."
        ),
    )
    parser.add_argument(
        "-s",
        "--solver",
        default="./glucose/simp/glucose",
        type=str,
        help=(
            "The SAT solver to be used."
        ),
    )
    parser.add_argument(
        "-v",
        "--verb",
        default=1,
        type=int,
        choices=range(0,2),
        help=(
            "Verbosity of the SAT solver used."
        ),
    )
    args = parser.parse_args()

    grid = (read_input_to_grid(args.input))

    cnf, nr_vars = encode(grid)

    result = call_solver(cnf, nr_vars, args.output, args.solver, args.verb)

    model = glucose_result_to_model(result)

    if model is None:
        black_cells = None
    else:
        black_cells = model_to_black_cells(model, len(grid))

    print_result(grid, black_cells)
