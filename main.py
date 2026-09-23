import json
import math
import sys
import csv

def load_data(file_path):
    #Load JSON data from the given file.
    with open(file_path, "r") as file:
        return json.load(file)


def normalize_data(data):
    """
    Convert supported input schemas into one consistent internal format.

    Internal format:
    warehouses -> {"W1": [x, y], ...}
    agents     -> {"A1": [x, y], ...}
    packages   -> [{"id": "P1", "warehouse": "W1",
                    "destination": [x, y]}, ...]
    """

    # Warehouses 
    if isinstance(data["warehouses"], list):
        warehouses = {
            warehouse["id"]: warehouse["location"]
            for warehouse in data["warehouses"]
        }
    else:
        warehouses = data["warehouses"]

    # Agents 
    if isinstance(data["agents"], list):
        agents = {
            agent["id"]: agent["location"]
            for agent in data["agents"]
        }
    else:
        agents = data["agents"]

    # Packages
    packages = []

    for package in data["packages"]:
        normalized_package = {
            "id": package["id"],
            "warehouse": package.get(
                "warehouse",
                package.get("warehouse_id")
            ),
            "destination": package["destination"]
        }

        packages.append(normalized_package)

    return {
        "warehouses": warehouses,
        "agents": agents,
        "packages": packages
    }


def calculate_distance(point1, point2):
    #Calculate Euclidean distance between two [x, y] coordinates.
    return math.sqrt(
        (point2[0] - point1[0]) ** 2
        + (point2[1] - point1[1]) ** 2
    )

def agent_sort_key(agent_id):
    # Extract numeric part of an agent ID for deterministic sorting.
    return int(agent_id[1:])

def get_next_agent_id(agents):
    # Generate the next available numeric agent ID.
    highest_id = max(
        agent_sort_key(agent_id)
        for agent_id in agents
    )

    return f"A{highest_id + 1}"

def assign_packages(data):
    """
    Assign each package to the nearest agent.

    Tie-breaking rules:
    1. Minimum Euclidean distance to the warehouse.
    2. If distance is tied, choose the agent with fewer packages assigned.
    3. If still tied, choose the agent with the lowest agent ID.
    """

    assignments = {
        agent_id: []
        for agent_id in data["agents"]
    }

    for package in data["packages"]:
        warehouse_id = package["warehouse"]
        warehouse_location = data["warehouses"][warehouse_id]

        agent_distances = {}

        # Calculate distance of every agent from the warehouse
        for agent_id, agent_location in data["agents"].items():
            agent_distances[agent_id] = calculate_distance(
                agent_location,
                warehouse_location
            )

        # Find the minimum distance
        minimum_distance = min(agent_distances.values())

        # Find all agents tied at the minimum distance
        tied_agents = [
            agent_id
            for agent_id, distance in agent_distances.items()
            if math.isclose(distance, minimum_distance)
        ]

        # Tie-break:
        # 1. Fewest packages currently assigned
        # 2. Lowest agent ID
        selected_agent = min(
            tied_agents,
            key=lambda agent_id: (
                len(assignments[agent_id]),
                agent_sort_key(agent_id)
            )
        )

        assignments[selected_agent].append(package)

    return assignments

def assign_packages_with_midday_agent(data, new_agent_location):
    """
    Bonus simulation where a new agent joins mid-day.

    Assumptions:
    - Mid-day occurs after half of the packages have been processed.
    - The new agent is available only for the remaining packages.
    - Packages assigned before the new agent joins are not reassigned.
    - Normal distance and tie-breaking rules still apply.
    """

    # Make a copy so the original normalized data is not modified.
    agents = data["agents"].copy()

    assignments = {
        agent_id: []
        for agent_id in agents
    }

    new_agent_id = get_next_agent_id(agents)

    packages = data["packages"]

    # First half of packages are processed before the new agent joins.
    midpoint = len(packages) // 2

    for index, package in enumerate(packages):

        # New agent joins at mid-day.
        if index == midpoint:
            agents[new_agent_id] = new_agent_location
            assignments[new_agent_id] = []

            print(
                f"Mid-day: {new_agent_id} joined at "
                f"{new_agent_location}"
            )

        warehouse_id = package["warehouse"]
        warehouse_location = data["warehouses"][warehouse_id]

        agent_distances = {}

        for agent_id, agent_location in agents.items():
            agent_distances[agent_id] = calculate_distance(
                agent_location,
                warehouse_location
            )

        minimum_distance = min(agent_distances.values())

        tied_agents = [
            agent_id
            for agent_id, distance in agent_distances.items()
            if math.isclose(distance, minimum_distance)
        ]

        selected_agent = min(
            tied_agents,
            key=lambda agent_id: (
                len(assignments[agent_id]),
                agent_sort_key(agent_id)
            )
        )

        assignments[selected_agent].append(package)

    return assignments, new_agent_id

def calculate_total_distances(data, assignments):
    """
    Calculate total delivery distance for each agent.

    Delivery distance is measured from each package's warehouse
    to its destination. Agent-to-warehouse distance is used only
    for package assignment.
    """
    total_distances = {}

    for agent_id, packages in assignments.items():
        total_distance = 0.0

        for package in packages:
            warehouse_id = package["warehouse"]
            warehouse_location = data["warehouses"][warehouse_id]
            destination = package["destination"]

            delivery_distance = calculate_distance(
                warehouse_location,
                destination
            )

            total_distance += delivery_distance

        total_distances[agent_id] = total_distance

    return total_distances

def generate_report(assignments, total_distances):
    """
    Generate delivery statistics and identify the most efficient agent.

    Efficiency = average delivery distance per package.
    Lower efficiency means better performance.

    Best-agent tie-break:
    If efficiencies are equal, the agent with the lower numeric ID wins.
    """

    report = {}
    eligible_agents = []

    for agent_id, packages in assignments.items():
        packages_delivered = len(packages)
        total_distance = total_distances[agent_id]

        if packages_delivered > 0:
            efficiency = total_distance / packages_delivered

            eligible_agents.append(
                (efficiency, agent_sort_key(agent_id), agent_id)
            )
        else:
            efficiency = 0.0

        report[agent_id] = {
            "packages_delivered": packages_delivered,
            "total_distance": round(total_distance, 2),
            "efficiency": round(efficiency, 2)
        }

    if eligible_agents:
        best_agent = min(eligible_agents)[2]
    else:
        best_agent = None

    report["best_agent"] = best_agent

    return report

def export_top_performer_csv(report, file_path="top_performer.csv"):
    # Export the best-performing agent's statistics to a CSV file.

    best_agent = report["best_agent"]

    # No agent can be selected if no packages were delivered.
    if best_agent is None:
        print("No deliveries — skipping CSV export.")
        return False

    agent_data = report[best_agent]

    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "agent_id",
            "packages_delivered",
            "total_distance",
            "efficiency"
        ])

        writer.writerow([
            best_agent,
            agent_data["packages_delivered"],
            agent_data["total_distance"],
            agent_data["efficiency"]
        ])

    return True

def render_ascii_map(data, width=20, height=10):
    """
    Render an ASCII spatial map of warehouses, agents,
    and package destinations.

    Symbols:
    W = Warehouse
    A = Agent
    D = Package destination
    * = Multiple locations mapped to the same cell
    """

    # Collect all coordinates so they can be scaled
    # using the same coordinate range.
    warehouse_points = list(data["warehouses"].values())
    agent_points = list(data["agents"].values())
    destination_points = [
        package["destination"]
        for package in data["packages"]
    ]

    all_points = (
        warehouse_points
        + agent_points
        + destination_points
    )

    if not all_points:
        print("No locations available to visualize.")
        return

    # Find coordinate boundaries
    x_values = [point[0] for point in all_points]
    y_values = [point[1] for point in all_points]

    min_x = min(x_values)
    max_x = max(x_values)
    min_y = min(y_values)
    max_y = max(y_values)

    # Create empty grid
    grid = [
        [" " for _ in range(width)]
        for _ in range(height)
    ]

    def scale_point(point):
        """Convert real coordinates to ASCII grid coordinates."""
        x, y = point

        # Handle cases where every point has the same x-coordinate
        if max_x == min_x:
            grid_x = width // 2
        else:
            grid_x = round(
                (x - min_x)
                / (max_x - min_x)
                * (width - 1)
            )

        # Handle cases where every point has the same y-coordinate
        if max_y == min_y:
            grid_y = height // 2
        else:
            grid_y = round(
                (y - min_y)
                / (max_y - min_y)
                * (height - 1)
            )

        # Flip y-axis so larger y-values appear higher on screen
        grid_y = height - 1 - grid_y

        return grid_x, grid_y

    def place_point(point, symbol):
        """Place a symbol on the grid and mark collisions with '*'."""
        grid_x, grid_y = scale_point(point)

        if grid[grid_y][grid_x] == " ":
            grid[grid_y][grid_x] = symbol
        elif grid[grid_y][grid_x] != symbol:
            grid[grid_y][grid_x] = "*"
        else:
            # Multiple entities of the same type also count as an overlap
            grid[grid_y][grid_x] = "*"

    # Plot warehouses
    for location in warehouse_points:
        place_point(location, "W")

    # Plot agents
    for location in agent_points:
        place_point(location, "A")

    # Plot package destinations
    for location in destination_points:
        place_point(location, "D")

    # Print map
    print("\nASCII Delivery Map")
    print("+" + "-" * width + "+")

    for row in grid:
        print("|" + "".join(row) + "|")

    print("+" + "-" * width + "+")
    print("W = Warehouse")
    print("A = Agent")
    print("D = Package Destination")
    print("* = Multiple locations")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "test_cases/base_case.json"
    midday_mode = "--midday-agent" in sys.argv
    
    try:
        data = load_data(input_file)
    except FileNotFoundError:
        print(f"Error: input file not found: {input_file}")
        sys.exit(1)

    normalized_data = normalize_data(data)

    if midday_mode:
        # Bonus scenario: new agent joins at [50, 75]
        assignments, new_agent_id = assign_packages_with_midday_agent(
            normalized_data,
            [50, 75]
        )

        # Add the new agent to normalized data so bonus visualizations
        # can also display the new agent.
        normalized_data["agents"][new_agent_id] = [50, 75]

    else:
        assignments = assign_packages(normalized_data)

    # Calculate total delivery distance
    total_distances = calculate_total_distances(
        normalized_data,
        assignments
    )

    # Generate final report
    report = generate_report(
        assignments,
        total_distances
    )

    # Validate: every package must be accounted for
    total_packages = len(normalized_data["packages"])
    total_delivered = sum(len(p) for p in assignments.values())

    if total_delivered != total_packages:
        raise ValueError(
            f"Delivered {total_delivered}/{total_packages} packages "
            f"— assignment logic dropped or duplicated packages."
        )

    # Save report to JSON file
    with open("report.json", "w") as file:
        json.dump(report, file, indent=4)
        
    # Bonus: Export top-performing agent to CSV
    csv_exported = export_top_performer_csv(report)   

    print("Simulation completed successfully.")
    print(f"{total_delivered}/{total_packages} packages delivered.")
    print("Report saved to report.json")
    if csv_exported:
        print("Top performer saved to top_performer.csv")
        
    # Bonus: Display ASCII spatial map
    render_ascii_map(normalized_data)    