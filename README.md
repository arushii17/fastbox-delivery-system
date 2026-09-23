# FastBox Mystery Delivery System

A Python-based logistics simulation developed for the **Mystery Delivery System** assignment.

The program simulates package assignment and delivery for FastBox, where packages originate from different warehouses and are assigned to the nearest available delivery agent. It calculates delivery distances, evaluates agent efficiency, generates a JSON report, and includes additional visualization and simulation features.

## Features

* Reads delivery data from JSON files
* Supports multiple input JSON structures through schema normalization
* Assigns packages to the nearest agent using Euclidean distance
* Handles assignment ties deterministically
* Calculates total delivery distance for every agent
* Calculates average delivery distance per package as the efficiency metric
* Identifies the most efficient delivery agent
* Validates that every package has been assigned
* Generates the final results in `report.json`
* Supports custom input files through the command line

### Bonus Features

* Exports the top-performing agent to `top_performer.csv`
* Displays warehouses, agents, and package destinations using an ASCII spatial map
* Supports an optional simulation where a new delivery agent joins mid-day

---

## Project Structure

```text
fastbox-delivery-system/
│
├── main.py
├── README.md
├── report.json
├── top_performer.csv
│
└── test_cases/
    ├── base_case.json
    ├── test_case_1.json
    ├── test_case_2.json
    ├── test_case_3.json
    ├── test_case_4.json
    ├── test_case_5.json
    ├── test_case_6.json
    ├── test_case_7.json
    ├── test_case_8.json
    ├── test_case_9.json
    └── test_case_10.json
```

## Requirements

* Python 3.x
* No external Python libraries are required

The project uses only Python standard-library modules:

* `json`
* `math`
* `sys`
* `csv`

---

## Running the Program

### Default Simulation

Running the program without an input argument uses:

```text
test_cases/base_case.json
```

Run:

```bash
python main.py
```

### Run a Different Test Case

Provide the JSON file path as the first command-line argument:

```bash
python main.py test_cases/test_case_5.json
```

The generated `report.json` and `top_performer.csv` correspond to the input file used for the current simulation.

### Mid-Day Agent Bonus

The optional mid-day-agent simulation can be enabled with:

```bash
python main.py test_cases/base_case.json --midday-agent
```

In this bonus scenario, a new agent is automatically assigned the next available agent ID and joins at coordinate:

```text
[50, 75]
```

The new agent participates only in assignments made after the mid-day point.

---

## Input Handling

The supplied JSON files use slightly different structures, so the program normalizes the input before running the simulation.

For example, warehouses and agents may be represented as lists:

```json
{
    "warehouses": [
        {
            "id": "W1",
            "location": [0, 0]
        }
    ]
}
```

or as dictionaries:

```json
{
    "warehouses": {
        "W1": [0, 0]
    }
}
```

Packages may also reference their warehouse using either:

```text
warehouse
```

or:

```text
warehouse_id
```

Both structures are converted into a consistent internal representation before package assignment.

---

## Package Assignment

Each package is assigned based on the Euclidean distance between the agent's location and the package's warehouse.

The distance is calculated as:

```text
distance = sqrt((x2 - x1)^2 + (y2 - y1)^2)
```

The agent with the minimum distance to the warehouse receives the package.

### Tie-Breaking

If multiple agents are equally close to a warehouse, the following deterministic rules are applied:

1. Select the agent with the fewest packages currently assigned.
2. If the agents are still tied, select the agent with the lowest numeric agent ID.

For example, if `A2` and `A10` remain tied, `A2` is selected.

---

## Delivery Distance Assumption

Agent-to-warehouse distance is used to determine **which agent receives a package**.

For delivery statistics, total distance traveled is calculated as the sum of the Euclidean distances from each package's warehouse to its destination:

```text
Warehouse → Package Destination
```

Therefore:

```text
Agent-to-Warehouse Distance = Assignment decision
Warehouse-to-Destination Distance = Delivery distance
```

The simulation assumes that agents collect their assigned packages from their respective warehouses.

Return trips to warehouses and route/path optimization between multiple destinations are not included.

---

## Efficiency

Agent efficiency is calculated as:

```text
efficiency = total_delivery_distance / packages_delivered
```

This represents the **average delivery distance per package**.

A lower value represents better efficiency.

Agents that deliver zero packages are reported with an efficiency of `0.0`, but they are excluded when selecting the best-performing agent.

If two eligible agents have identical efficiency values, the agent with the lower numeric agent ID is selected.

---

## Output

The program generates a `report.json` file containing statistics for every agent.

Example:

```json
{
    "A1": {
        "packages_delivered": 2,
        "total_distance": 64.14,
        "efficiency": 32.07
    },
    "A2": {
        "packages_delivered": 2,
        "total_distance": 36.18,
        "efficiency": 18.09
    },
    "A3": {
        "packages_delivered": 1,
        "total_distance": 7.07,
        "efficiency": 7.07
    },
    "best_agent": "A3"
}
```

Distances and efficiency values are rounded to two decimal places in the final report.

---

## Package Validation

After package assignment, the program verifies:

```text
total packages assigned == total packages in input
```

If the numbers do not match, the simulation raises an error instead of generating an incomplete delivery result.

This ensures that no package is accidentally dropped during assignment.

---

## Bonus: Top Performer CSV

The most efficient eligible agent is exported to:

```text
top_performer.csv
```

Example:

```csv
agent_id,packages_delivered,total_distance,efficiency
A3,1,7.07,7.07
```

If there are no completed deliveries, CSV export is skipped.

---

## Bonus: ASCII Delivery Map

The program displays a normalized ASCII spatial representation of the delivery system in the terminal.

Example:

```text
ASCII Delivery Map
+--------------------+
|             D      |
|       D W          |
|                    |
|           A        |
|         A          |
|     D              |
|                 A  |
|                  WD|
|  D                 |
|WA                  |
+--------------------+

W = Warehouse
A = Agent
D = Package Destination
* = Multiple locations
```

The map scales the actual coordinates to a fixed terminal grid.

Symbols:

* `W` — Warehouse
* `A` — Agent
* `D` — Package destination
* `*` — Multiple locations mapped to the same grid cell

The visualization is intended as a spatial overview. It does not perform route or path optimization.

---

## Bonus: New Agent Joining Mid-Day

The simulation optionally supports a new delivery agent joining during the day.

Run:

```bash
python main.py test_cases/base_case.json --midday-agent
```

### Assumptions

For this optional scenario:

1. Mid-day occurs after half of the packages have been processed.
2. The new agent receives the next available numeric agent ID.
3. The demonstration agent joins at `[50, 75]`.
4. Packages assigned before the agent joins remain with their original agents.
5. The new agent participates only in assignment decisions for the remaining packages.
6. The standard nearest-agent and tie-breaking rules continue to apply.

For an odd number of packages, integer division determines the midpoint. For example, with five packages, the first two are processed before the new agent joins and the remaining three are processed afterward.

---

## Testing

The solution was tested using:

* The supplied base case
* All 10 supplied test cases
* Different numbers and locations of warehouses
* Different numbers and locations of agents
* Different package distributions
* Agents receiving zero packages
* Package-assignment ties

For every supplied input, the validation check confirmed that:

```text
packages delivered == total packages
```

A custom tie scenario was also used to verify that equal-distance assignments follow the documented workload and agent-ID tie-breaking rules.

---

## Key Assumptions

Where behavior was not explicitly defined, the following deterministic assumptions were used:

1. Package assignment is based on Euclidean distance from an agent to the package's warehouse.
2. Equal-distance assignments are resolved first by current workload and then by numeric agent ID.
3. Agent IDs follow the `A<number>` format used by the supplied input data.
4. Delivery distance is measured from the warehouse to the destination for each package.
5. Agent-to-warehouse distance is used only for package assignment.
6. Return trips and multi-package route optimization are outside the scope of the simulation.
7. Efficiency represents average delivery distance per delivered package, and lower values are considered more efficient.
8. Agents with no deliveries are excluded from best-agent selection.
9. The optional mid-day simulation does not reassign packages that were already assigned before the new agent joined.

---

## Author

**Arushi Bhat**

Python Developer Assignment
FastBox Mystery Delivery System
