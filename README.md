# General information and compiling

This project solves the logic puzzle Hitori by reduction to SAT (propositional logic), as a homework for Propositional and Predicate Logic (NAIL062). The Python code encodes the puzzle into a CNF formula, solves it with a SAT solver and decodes the result.

The SAT solver used is [Glucose](https://www.labri.fr/perso/lsimon/research/glucose/), more specifically Glucose 4.2.1. The source code is compiled using

```
cd glucose/simp
make
cd ../..
```
After this, the executable file will be located at `glucose/simp/glucose`. You must run `hitori.py` **from the root of the repository**, because the default path to the solver is relative (`./glucose/simp/glucose`).

Note that the solver, as well as the Python script, are assumed to work on UNIX-based systems. In case you prefer using Windows, I recommend to use WSL.


# Mathematical description of the Hitori problem

More information about the puzzle may be found [online](https://en.wikipedia.org/wiki/Hitori).

Hitori is played with a grid of squares or cells, with each cell initially containing a number. The game is played by eliminating numbers (white squares) and this is done by coloring them black. The objective is to transform the grid to a state wherein all three following rules are true:

1. no row or column can have more than one occurrence of any given number among the white cells
2. black cells cannot be horizontally or vertically adjacent, although they can be diagonal to one another
3. the remaining numbered (white) cells must be all connected to each other, horizontally or vertically

**Parameters** A size $n \in \mathbb{N}$ and a grid $a \in \{1,\dots,n\}^{n \times n}$, where $a[r][c]$ is the number in the cell $(r,c)$, $r,c \in \{0,\dots,n-1\}$. Two cells are adjacent if they differ by exactly 1 in exactly one coordinate (diagonal cells are not adjacent).

**What we look for** A set $B \subseteq \{0,\dots,n-1\}^2$ of **black** cells. The remaining cells are **white**.

**Decision variables** For every cell $(r,c)$ one Boolean variable $x(r,c)$, which is true if and only if the cell is black (i.e. $(r,c) \in B$).

**Constraints**

1. For every two distinct cells $p, q$ in the same row (or in the same column) with $a[p] = a[q]$: $p \in B$ or $q \in B$.
2. For every two adjacent cells $p, q$: not both $p \in B$ and $q \in B$.
3. The graph whose vertices are the cells outside $B$ and whose edges join adjacent cells is connected.

**Solution.** A solution is any set B satisfying constraints 1–3 (uniqueness is not required). If there is no such set, the puzzle is unsolvable.

An example of a valid input format is:

```
3
1 1 2
2 3 1
3 2 1
```

Where the first line is size of the grid.
And all other lines are the actual grid.

The target output is:

```
■ 1 2 
2 3 ■ 
3 2 1 
```

# Description of CNF encoding

For each cell (r, c), there is one Boolean variable `x(r,c)`.
It is true when the cell is **black**. There are $n^2$ variables in total. The variable index is `n·r + c + 1`. The literal `black(r,c)` is represented as `+index`, and the literal `white(r,c)` as `−index`.

### Clause 1. No row or column can have more than one occurrence of any given number

For every pair of distinct cells p, q in the same row or the same column such that a[p] = a[q]:

`x(p) ∨ x(q)`

If a row (or column) contains two identical numbers, at least one of them must be black. Otherwise, both would remain white, and the number would be repeated. In the code, this is handled by the `encode_basic_rules` function, which includes two sets of loops (one for rows and one for columns) and the clause `[black(p), black(q)]`.

### Clause 2. Black cells cannot be adjacent

For each pair of cells p, q that are adjacent to the right or to the bottom:

`¬x(p) ∨ ¬x(q)`

Two adjacent cells cannot be black at the same time: at least one of them is white. It is enough to check the neighbor on the right and the neighbor below, because each pair of cells occurs exactly once. In the code: `encode_basic_rules`, clause `[white(p), white(q)]`.

### Clause 3. All white cells are connected

Connectivity cannot be expressed directly via a short formula, so I added connectivity clauses only when they are needed:

1. Solve the formula derived from constraints 1–2 using the Glucose solver.
2. If the solver returns UNSAT, the puzzle has no solution.
3. Otherwise, `find_white_components(n, black_cells)` takes the coloring found by the solver and, by traversing the graph, partitions the white cells into connected components (islands). If there is only one such component, the solution is valid.
4. Otherwise, for every island except the largest one, `disconnected_island_clause(n, island, other_cell)` constructs a clause, which is added to the formula:

   `⋁_{c ∈ I} x(c)  ∨  ⋁_{b ∈ boundary(I)} ¬x(b)  ∨  x(w)`

   where `I` is the island, `boundary(I)` consists of cells outside `I` that are adjacent to cells in `I`, and `w` is a cell belonging to a different island (specifically, one within the largest connected component).

5. `solve(...)` executes this as a loop: it solves the formula, identifies the islands, adds the clauses from step 4, and then solves the formula again. This process repeats until only one connected component remains or the formula becomes unsatisfiable.

# Alternatives

**One island per iteration (my initial version)** 

In the first version of `solve`, after each solver run, a connectivity clause was added for only one of the islands formed by the white cells. The clause itself is the same as the one used in the chosen approach (it forbids a clause where all cells of an island are white, its entire boundary consists of black cells, and at least one cell belonging to a different island is also white—effectively meaning the island is cut off from the rest).
This clause does not rule out valid solutions. However, any disconnected coloring found by the solver will violate it, causing the loop to terminate. On larger instances. But this approach proved to be significantly slower than the one ultimately selected. A detailed comparison with the chosen approach is provided in the "Experiments" section.

# User documentation

Basic usage: 

```
hitori.py [-h] [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v {0,1}]
```

Command-line options:
| Parameter | Value | Default |
|---|---|---|
| `-i`, `--input` | puzzle file | `input.in` |
| `-o`, `--output` | file to which the CNF formula (DIMACS) is written | `formula.cnf` |
| `-s`, `--solver` | path to the SAT solver | `./glucose/simp/glucose` |
| `-v`, `--verb` | solver output verbosity: 0 or 1 | 1 |

### Input format

The first line is the size of n. 
Next are n lines with n numbers from 1 to n separated by spaces.

```
4
2 1 3 3
1 3 2 1
3 4 1 2
4 2 3 1
```

### Output format

For each solution, the final grid is printed, with black cells replaced by the symbol `■`:

```

##################################################################
##################[ Solution of Hitori problem ]#################
##################################################################

2 1 ■ 3
■ 3 2 1
3 4 1 2
4 2 3 ■
```
If there is no solution, `This grid has no solution` is printed instead of the grid.

### Code Structure

| Function | Purpose |
|---|---|
| `read_input_to_grid` | Reads a file and returns a grid |
| `cell_to_number`, `black`, `white` | Maps cells to variable numbers and literals |
| `encode_basic_rules` | Encodes constraint clauses 1 and 2 |
| `call_solver` | Writes a DIMACS file and executes the Glucose solver |
| `glucose_result_to_model` | Extracts a model from the solver's output |
| `model_to_black_cells` | Identifies the set of black cells based on the model |
| `neighbors`, `find_white_components` | Finds cell neighbors and identifies connected components of white cells |
| `disconnected_island_clause` | Generates a clause to prevent isolated components |
| `solve` | Main loop: solve, then check connectivity, and add clauses |
| `print_result` | Outputs the final result |

# Example instances

* `input-2by2-unsat.txt`: An easy, unsolvable 2x2 instance.
```
2
1 1
1 1
```
Output:
```
This grid has no solution
```

* `input-3by3-sat.txt`: An easy, solvable 3x3 instance
```
3
1 1 2
2 3 1
3 2 1
```
Output:
```
■ 1 2
2 3 ■
3 2 1
```

* `input-4by4-sat.txt`: An easy, solvable 4x4 instance
```
4
2 1 3 3
1 3 2 1
3 4 1 2
4 2 3 1
```
Output:
```
2 1 ■ 3
■ 3 2 1
3 4 1 2
4 2 3 ■
```

* `input-9by9-unsat.txt`: A medium, unsolvable 9x9 instance
```
9
1 5 3 4 5 6 7 8 9
5 5 5 2 6 7 8 9 1
3 5 5 6 7 8 9 1 2
4 2 6 7 8 9 1 2 3
5 6 7 8 9 1 2 3 4
6 7 8 9 1 2 3 4 5
7 8 9 1 2 3 4 5 6
8 9 1 2 3 4 5 6 7
9 1 2 3 4 5 6 7 8
```
Output:
```
This grid has no solution
```

* `input-17by17-sat.txt`: A hard, solvable 17x17 instance
```
17
17 1 7 5 11 6 11 10 2 10 13 17 16 17 8 14 13
14 15 10 10 3 13 9 7 15 12 12 11 17 16 15 15 4
2 13 6 7 9 5 16 4 15 3 16 11 1 11 9 10 9
8 9 13 3 1 11 4 12 16 5 10 16 9 11 14 2 7
12 9 3 3 2 7 13 13 4 17 10 15 11 15 1 17 17
10 9 8 3 14 12 12 15 3 13 10 7 12 5 4 17 9
13 5 11 10 4 6 16 8 17 1 15 14 3 7 6 13 12
13 7 2 17 16 10 3 6 4 14 9 5 12 15 4 4 9
13 3 2 15 7 8 15 9 6 8 9 1 7 8 10 17 5
3 15 2 1 7 17 10 5 12 6 9 13 14 2 13 11 16
3 16 15 2 10 11 17 11 11 11 3 6 13 12 13 17 1
7 11 16 2 9 1 2 2 10 4 2 14 6 3 13 5 17
11 4 16 9 15 17 11 7 16 12 2 10 8 7 5 7 3
5 14 4 3 17 3 12 11 13 8 6 17 10 9 2 7 15
11 17 1 13 12 14 4 9 15 10 4 2 5 8 7 7 6
11 2 1 14 12 15 6 17 7 16 4 4 5 10 15 8 13
11 10 1 8 12 16 5 13 9 11 5 9 2 6 3 13 14
```
Output:
```
■ 1 7 5 11 6 ■ 10 2 ■ 13 17 16 ■ 8 14 ■
14 ■ 10 ■ 3 13 9 7 ■ 12 ■ 11 17 16 ■ 15 4
2 13 6 7 ■ 5 ■ 4 15 3 16 ■ 1 ■ 9 10 ■
8 ■ 13 ■ 1 ■ 4 12 ■ 5 ■ 16 9 11 14 2 7
12 9 ■ 3 2 7 13 ■ 4 ■ 10 15 11 ■ 1 17 ■
10 ■ 8 ■ 14 12 ■ 15 3 13 ■ 7 ■ 5 4 ■ 9
■ 5 11 10 4 ■ 16 8 17 1 15 ■ 3 7 6 13 12
13 7 ■ 17 16 10 3 6 ■ 14 ■ 5 12 15 ■ 4 ■
■ 3 2 ■ 7 ■ 15 ■ 6 ■ 9 1 ■ 8 10 ■ 5
3 15 ■ 1 ■ 17 10 5 12 6 ■ 13 14 2 ■ 11 16
■ 16 15 2 10 ■ 17 ■ 11 ■ 3 6 ■ 12 13 ■ 1
7 11 16 ■ 9 1 ■ 2 10 4 ■ 14 6 3 ■ 5 17
■ 4 ■ 9 15 ■ 11 ■ 16 ■ 2 10 8 ■ 5 ■ 3
5 14 4 ■ 17 3 12 11 13 8 6 ■ 10 9 2 7 15
■ 17 ■ 13 ■ 14 ■ 9 ■ 10 4 2 5 ■ 7 ■ 6
11 2 1 14 12 15 6 17 7 16 ■ 4 ■ 10 ■ 8 13
■ 10 ■ 8 ■ 16 ■ 13 ■ 11 5 9 2 6 3 ■ 14
```

## Regarding the instance that takes longer than 10 seconds to solve

Among our test cases, there are no solvable instances that take more than 10 seconds to solve using the final version of our program. All of them—including the largest one (17×17)—are solved in a fraction of a second. To try and find such an instance, I selected a large 17×17 puzzle from a public dataset.
<https://github.com/SmilingWayne/puzzlekit>

 The first version of the `solve` function failed to complete within 60+ minutes (at which point I stopped the program). After modifying `solve`, the same instance was solved in 5 iterations, taking approximately 0.1 seconds. A detailed comparison of the two versions is provided in the "Experiments" section.

As for finding an instance that would take more than 10 seconds to solve, I found a report from Columbia University stating that a CDCL solver solved a 20×20 grid in 0.042 seconds. <https://www.cs.columbia.edu/~sedwards/classes/2023/4995-fall/reports/Hitori-report.pdf>

Unfortunately, I have been unable to find any other solvable instances of this size in publicly available datasets that our final algorithm cannot solve quickly.

# Experiments

Experiments were run on  MacBook Air M4, 16 GB

No separate script was used.

For each example, I ran `time python3 hitori.py -i <file> -v 0` and recorded the following:
- iterations - the number of times the Glucose solver was invoked during the solution process (i.e., the number of times a disconnected coloring was found, plus one);
- time — the total execution time of the program.

| Instance | Size | Result | First version: iterations / time | Second version: iterations / time |
|---|---|---|---|---|
| `input-2by2-unsat.txt` | 2×2 | UNSAT | 3 / ~0.07 s | 3 / ~0.07 s |
| `input-3by3-sat.txt` | 3×3 | SAT | 1 / ~0.05 s | 1 / ~0.06 s |
| `input-4by4-sat.txt` | 4×4 | SAT | 15 / 0.10 s | 2 / 0.07 s |
| `input-9by9-unsat.txt` | 9×9 | UNSAT |  - | 4 / ~0.09 s |
| `input-17by17-sat.txt` | 17×17 | SAT | did not finish within 60+ minutes | 5 / ~0.1 s |

In the results, I mention two versions of the `solve` function. This is because, when running the 17x17 test case, the program failed to find a solution even after an hour—whereas all other cases were solved in a fraction of a second—so I modified the code:

**First version (one island per iteration).** 

```python
island = components[0]
other_cell = next(iter(components[1]))
cnf.append(disconnected_island_clause(n, island, other_cell))
```

**Second version (all islands except the largest one).** 

```python
components.sort(key=len)
other_cell = next(iter(components[-1]))      # a cell from the largest component
for island in components[:-1]:               # all other islands
    cnf.append(disconnected_island_clause(n, island, other_cell))
```

This happened because, after each run of the solver, it would only forbid one of the "islands" into which the white cells had fragmented. The other defects remained, so the solver would generate a new coloring where one island was fixed, but a disconnection would emerge elsewhere. For a 4×4 grid, this required 15 solver runs; for a 17×17 grid, the coloring would immediately split into 8 islands, making it far too time-consuming to address them one by one.

The second version forbids all islands simultaneously, except for the largest one. These conditions are independent: each one prevents a specific island from being cut off from the rest. The solver accounts for all of them in a single run, correcting every defect at once. Each such clause eliminates an entire family of invalid colorings—specifically, any configuration where a given island is white while its boundary is black—rather than just a single instance. As a result, the number of islands decreases rapidly, and only five iterations were needed. Both approaches are equally correct; the only difference lies in the number of clauses applied per iteration.

## Sources
* Wikipedia, Hitori: <https://en.wikipedia.org/wiki/Hitori>
* Picat file with Hitori examples (contains the 17×17 puzzle): <https://hakank.org/picat/hitori.pi>
* PuzzleSolver (the 17×17 puzzle is the file `131_17x17.txt`): <https://github.com/SmilingWayne/PuzzleSolver>
* Report from Columbia University: <https://www.cs.columbia.edu/~sedwards/classes/2023/4995-fall/reports/Hitori-report.pdf>
* Glucose 4.2.1 SAT solver: <https://www.labri.fr/perso/lsimon/research/glucose/>
