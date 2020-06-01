from __future__ import annotations
from functools import reduce
import csv
import copy
from typing import Any, List, Optional, TypeVar, Tuple
from wgups.time import Time
from wgups.data_structures import ChainingHashTable, AMGraph
from wgups.models import Location, Package, PackageStatus, PackageStatusLog, Truck, TruckStatus, TruckStatusLog
from wgups.utilities import str_to_int_or_none, debug

StatusEnum = TypeVar("StatusEnum")
StatusLog = TypeVar("StatusLog")


# The Hub contains the logic for loading and managing the Package and Location data. It stores
# the data into the appropriate data structures and orchestrates the delivery simulation. All
# information regarding the simulation is logged for retrieval and analysis once the simulation is complete.
class Hub:
    def __init__(self, name: str, location: Location, start_time: Time):
        self.name = name
        self.current_time = copy.copy(start_time)  # Don't update the ref
        self.start_time = start_time
        self.location = location
        self.trucks = ChainingHashTable()
        self.packages = ChainingHashTable()
        self.trucks_log = ChainingHashTable()
        self.packages_log = ChainingHashTable()
        self.locations = AMGraph()

        self.__init_location_data()
        self.__init_truck_data()
        self.__init_package_data()

    # Run the simulations until all packages have been delivered
    def run(self) -> None:
        while self.__is_packages_to_deliver() or self.__trucks_out():
            self.update()
            self.current_time.add_minutes(1)

    # Called each minute of the simulation. Used to call any methods that need to recalculate and update
    # new state for packages and trucks based on the time.
    def update(self) -> None:
        self.__update_pending_packages()
        self.__update_trucks()

    # Track a package or truck as its status changes so we know the state of all
    # packages and trucks at any given time.
    def log_status(self, item_id: int, new_status: StatusEnum, miles_traveled: int = 0.0,
                   route_traveled: List[Location] = [], next_destination: Location = None,
                   arrival_time: Time = None) -> None:
        # Determine if what type of status this is
        if isinstance(new_status, PackageStatus):
            new_status_update = PackageStatusLog(new_status, copy.copy(self.current_time))
            log = self.packages_log
        else:
            new_status_update = TruckStatusLog(new_status, miles_traveled, route_traveled, next_destination,
                                               arrival_time, copy.copy(self.current_time))
            log = self.trucks_log

        # If this has no history start a new list to store
        # its statuses and set its initial status
        if item_id not in log:
            new_package_history = [new_status_update]
            log.insert(item_id, new_package_history)
        # Otherwise, if the new status is not the same as the current (no real change), we
        # update the previous status with an end time add the new status to the existing list
        # with a minute added to the start time to ensure it doesn't conflict with the end time.
        else:
            # if log[item_id][-1].status == new_status:
            #     return

            end_time = copy.copy(self.current_time)
            if new_status_update.start_time == log[item_id][-1].start_time:
                new_status_update.start_time.add_minutes(1)
                end_time.add_minutes(1)

            log[item_id][-1].end_time = end_time
            log[item_id].append(new_status_update)

    # Methods to allow easy printing of summary stats on Hub, Trucks, and Packages
    def print_package_by_id(self, package_id: int, time: Time) -> None:
        # Get package data
        if package_id in self.packages:
            package_snapshot = copy.copy(self.packages[package_id])

        # Get log os status at time queried and set it on package data
        log = self.__get_log_by_id(package_id, time, self.packages_log)
        package_snapshot.status = log.status

        # Filter out any blank fields on the package data str
        def has_data(data: str):
            return "None" not in data and "N/A" not in data

        package_str = '\n'.join(filter(has_data, str(package_snapshot).split("\n")))
        package_str_w_timestamp = ''.join([
            f"{'-' * 85}\n",
            f"Package status last updated: {log.start_time}\n"
            f"{package_str}\n",
            '-' * 85
        ])

        print(package_str_w_timestamp)

    def print_all_packages(self, time: Time) -> None:
        print(f"{'=' * 85}\n")
        for package_id in self.packages.keys():
            self.print_package_by_id(package_id, time)
        print(f"Total Packages: {len(self.packages)}")
        print(f"{'=' * 85}\n")

    def print_truck_by_id(self, truck_id: int, time: Time, include_route: bool = False) -> None:
        package_logs = self.__get_package_logs_by_truck_id(truck_id, time)
        packages_loaded = list(filter(lambda k_v: k_v[1].status is PackageStatus.OUT_FOR_DELIVERY, package_logs))
        packages_delivered = list(filter(lambda k_v: k_v[1].status is PackageStatus.DELIVERED, package_logs))
        packages_delivered_late = list(filter(lambda k_v: k_v[1].status is PackageStatus.DELIVERED_LATE, package_logs))

        truck_log = self.__get_log_by_id(truck_id, time, self.trucks_log)
        route_str = ''

        if include_route:
            route = '->\n'.join([str(location) for location in truck_log.route_traveled])
            route_str = f"\nRoute traveled:\n{route}"

        truck_str_w_timestamp = ''.join([
            f"{'-' * 85}\n",
            f"Truck status last updated: {truck_log.start_time}\n"
            f"Truck ID: {truck_id}\t\tStatus: {truck_log.status.name}\n\n",
            f"Packages loaded: {[k_v[0] for k_v in packages_loaded]}\n",
            f"Packages delivered: {[k_v[0] for k_v in packages_delivered]}\n",
            f"Packages delivered late: {[k_v[0] for k_v in packages_delivered_late]}\n\n",
            f"Next destination: {truck_log.next_destination}\n",
            f"Arrival time: {truck_log.arrival_time}\n\n",
            f"Total miles traveled: {truck_log.miles_traveled}\n",
            route_str,
            '-' * 85
        ])

        print(truck_str_w_timestamp)

    def print_all_trucks(self, time: Time, include_route: bool = False) -> None:
        for truck_id in self.trucks.keys():
            self.print_truck_by_id(truck_id, time, include_route)

    def print_stats(self, time: Time = Time(0)):
        time = self.current_time if time == Time(0) else time
        time_operated = time - self.start_time

        package_logs = [(p_id, self.__get_log_by_id(p_id, time, self.packages_log)) for p_id in self.packages.keys()]
        pending = [p_id for p_id, log in package_logs if log.status is PackageStatus.PENDING]
        out_for_delivery = [p_id for p_id, log in package_logs if log.status is PackageStatus.OUT_FOR_DELIVERY]
        delivered = [p_id for p_id, log in package_logs if log.status is PackageStatus.DELIVERED]
        delivered_late = [p_id for p_id, log in package_logs if log.status is PackageStatus.DELIVERED_LATE]

        truck_logs = [(t_id, self.__get_log_by_id(t_id, time, self.trucks_log)) for t_id in self.trucks.keys()]
        total_miles_traveled = reduce(lambda stored, k_v: stored + k_v[1].miles_traveled, truck_logs, 0.0)
        trucks_used = [t_id for t_id, log in truck_logs if log.miles_traveled > 0.0]

        # Build package status details to print for each truck used
        trucks_str = ''

        def is_on_truck(package_id: int):
            return self.packages[package_id].truck_id == truck_id

        for truck_id in trucks_used:
            trucks_str += f"Truck {truck_id}:\n"
            trucks_str += ''.join([
                f"\tPackages out for delivery: {[p_id for p_id in out_for_delivery if is_on_truck(p_id)]}\n"
                f"\tPackages delivered: {[p_id for p_id in delivered if is_on_truck(p_id)]}\n",
                f"\tPackages delivered late: {[p_id for p_id in delivered_late if is_on_truck(p_id)]}\n",
            ])

        hub_stats = ''.join([
            f"{'-' * 32} Today the WGUPS Hub {'-' * 32}\n",
            f"Hours of operation: {self.start_time} to {time}",
            f"\t({time_operated[0]} Hrs and {time_operated[1]} Min)\n",
            f"Total number of packages handled: {len(self.packages)}\n",
            f"Number of trucks used: {len(trucks_used)}\n",
            f"Packages pending: {pending}\n",
            trucks_str,
            f"Total miles traveled for deliveries: {total_miles_traveled:.2f} Miles\n",
            '-' * 85
        ])

        print(hub_stats)

    # Getters to simplify log retrieval for Trucks and Packages
    def __get_package_logs_by_truck_id(self, truck_id: int, time: Time) -> Tuple[int, PackageStatusLog]:
        logs = []
        for package_id in self.packages.keys():
            log = self.__get_log_by_id(package_id, time, self.packages_log)
            on_truck = log.status is not PackageStatus.PENDING and log.status is not PackageStatus.READY_FOR_PICKUP
            if self.packages[package_id].truck_id == truck_id and on_truck:
                logs.append((package_id, log))
        logs.sort(key=lambda l: l[1].start_time, reverse=True)
        return logs

    def __get_log_by_id(self, item_id: int, time: Time, logs: ChainingHashTable) -> StatusLog:
        items_log = logs[item_id]
        for log in items_log:
            before_log_end = log.end_time == Time(0) or time < log.end_time
            if log.start_time <= time and before_log_end:
                return log

    # Check if Trucks need to be docked or loaded and sent out for deliveries
    def __update_trucks(self) -> None:
        for truck in self.trucks.values():
            # If truck has returned to the hub set the status as such
            at_hub = truck.next_destination == self.location and truck.arrival_time <= self.current_time
            if truck.status is TruckStatus.OUT_FOR_DELIVERIES and at_hub:
                truck.dock_at_hub()
            # If at the Hub, check if it needs to be loaded with packages
            if truck.status is TruckStatus.AT_HUB:
                self.__load_truck_with_packages(truck.id)
            # Pass it current time so it can determine it's location and next arrival time
            truck.update_state(self.current_time)

    # Check if Pending packages have arrived and are ready for delivery
    def __update_pending_packages(self) -> None:
        for package in self.packages.values():
            if package.status is PackageStatus.PENDING:
                if package.arrival_time <= self.current_time:
                    package.status = PackageStatus.READY_FOR_PICKUP
                    self.log_status(package.id, package.status)
                else:
                    self.log_status(package.id, package.status)

    # Find out if any more packages are at the Hub and need delivery
    def __is_packages_to_deliver(self) -> bool:
        for package in self.packages.values():
            if package.status is not PackageStatus.DELIVERED and package.status is not PackageStatus.DELIVERED_LATE:
                return True
        return False

    # Helps determine if based on package arrival times and delivery deadlines this is
    # a good time to load a truck an send it out for deliveries.
    def __is_time_to_load_truck(self, truck_id: int) -> bool:
        time_threshold = copy.copy(self.current_time).add_hours(1).add_minutes(15)
        truck_capacity = self.trucks[truck_id].package_capacity

        def __package_needs_delivery(p: Package) -> bool:
            return p.status is PackageStatus.PENDING or p.status is PackageStatus.READY_FOR_PICKUP

        packages_to_deliver = list(filter(__package_needs_delivery, self.packages.values()))
        min_delivery_deadline = time_threshold
        min_arrival_time = time_threshold
        assigned_truck_ids = []

        for package in packages_to_deliver:
            # Are the delivery deadlines close enough to the current time that a truck should be loaded
            if package.delivery_deadline != Time(0) and package.delivery_deadline < min_delivery_deadline:
                min_delivery_deadline = package.delivery_deadline
            # Are the arrival times of any packages close enough to wait to load the truck
            if package.arrival_time != Time(0) and package.arrival_time < min_arrival_time:
                if package.arrival_time > self.current_time:
                    min_arrival_time = package.arrival_time
            # What truck ids are packages assigned to
            if package.truck_id is not None:
                assigned_truck_ids.append(package.truck_id)

        # Determine if we can fit all packages on a truck and one or more have a truck already assigned
        remaining_packages_have_truck = len(packages_to_deliver) <= truck_capacity and len(assigned_truck_ids) > 0

        if min_delivery_deadline < time_threshold:
            return True
        elif min_arrival_time < time_threshold:
            return False
        elif remaining_packages_have_truck and truck_id not in assigned_truck_ids:
            return False
        else:
            return True

    def __trucks_out(self) -> bool:
        for truck in self.trucks.values():
            if truck.status is TruckStatus.OUT_FOR_DELIVERIES:
                return True
        return False

    # Determine based on delivery locations, pre-assigned trucks, and deadlines which packages need to
    # go out for delivery on the truck being loaded. Average space complexity of O(1) with a worst case of O(n)
    # and the time complexity derived from O(4n + 2nlogn) is O(n).
    def __load_truck_with_packages(self, truck_id: int) -> None:
        # Ensure truck is at the HUB, has package space remaining, and its an optimal time to load
        truck = self.trucks[truck_id]
        package_capacity_left = truck.package_capacity - len(truck.package_ids)
        no_capacity = package_capacity_left == 0
        truck_out = truck.status is not TruckStatus.AT_HUB

        if truck_out or no_capacity or not self.__is_time_to_load_truck(truck_id):
            return

        # Get ids for packages ready to go out for delivery, keep track of any packages
        # not going on this truck that belong to a package group. The remaining group
        # members will need to be removed too.
        groups_to_remove = []

        def __can_be_loaded(package_id: int) -> bool:
            potential_package = self.packages[package_id]
            ready = potential_package.status is PackageStatus.READY_FOR_PICKUP
            ok_for_truck_id = potential_package.truck_id is None or potential_package.truck_id == truck_id
            package_group_id = potential_package.group_id

            if (not ready or not ok_for_truck_id) and package_group_id is not None:
                groups_to_remove.append(package_group_id)

            return ready and ok_for_truck_id

        # Narrow down packages currently ready to go out for delivery. Space complexity
        # of O(1) and time complexity of O(n).
        package_ids_to_deliver = list(filter(__can_be_loaded, self.packages.keys()))

        # Filter out and group members of packages we can't deliver currently. Space
        # complexity of O(1) and time complexity of O(n).
        package_ids_to_deliver = list(filter(lambda package_id: self.packages[package_id].group_id not in groups_to_remove,
                                          package_ids_to_deliver))

        # If no packages meet our criteria we can stop here, otherwise we start prioritizing packages
        # to determine what gets loaded.
        if len(package_ids_to_deliver) == 0:
            return

        # We want to ensure any packages that are required to be on a certain truck get loaded when that
        # truck is docked.
        def truck_id_cmp(package_id: int) -> Optional[int]:
            truck_id_to_sort = self.packages[package_id].truck_id
            return truck_id_to_sort is None, truck_id_to_sort

        # First, we sort by delivery location so when possible we can load packages being delivered to the
        # same location on one truck. We then prioritize any packages that must be delivered on the truck being loaded.
        # Space complexity of O(1) and time complexity O(nlogn).
        package_ids_to_deliver.sort(key=lambda package_id: (self.packages[package_id].location.key(),
                                                         truck_id_cmp(package_id)))

        # Identify all packages to be delivered that have deadlines and those that have no deadlines.
        # Space complexity of O(1) and time complexity of O(n).
        package_ids_w_deadline = list(filter(lambda package_id: self.packages[package_id].delivery_deadline != Time(0),
                                          package_ids_to_deliver))
        package_ids_no_deadline = list(filter(lambda package_id: self.packages[package_id].delivery_deadline == Time(0),
                                           package_ids_to_deliver))

        # Last, sort the list of
        # package ids based on delivery deadlines so we end up with a list
        # of package ids sorted by deadline, same location, required truck id. # Space complexity
        # of O(1) and time complexity O(nlogn).
        package_ids_w_deadline.sort(key=lambda package_id: self.packages[package_id].delivery_deadline)

        # Combine package ids with deadlines and those without into one list with the highest priority package id
        # as the first element.
        package_ids_to_deliver_by_deadline = [*package_ids_w_deadline, *package_ids_no_deadline]

        # While the truck has space and there are packages to go out we load the truck.
        while package_capacity_left > 0 and len(package_ids_to_deliver) > 0:
            # Get the package id with the next highest priority to potentially load
            potential_package_id = package_ids_to_deliver_by_deadline[0]

            # If this package belongs to a group and the truck can fit
            # all those in the group, load them. Space complexity of O(1) and
            # time complexity of O(n).
            group_id = self.packages[potential_package_id].group_id
            packages_loaded = []
            if group_id is not None:
                packages_in_group = list(
                    filter(lambda package_id: self.packages[package_id].group_id == group_id, package_ids_to_deliver))
                if len(packages_in_group) <= package_capacity_left:
                    for p_id in packages_in_group:
                        truck.package_ids.append(p_id)
                        packages_loaded.append(p_id)
            # Otherwise add this package with no group to the truck alone
            else:
                truck.package_ids.append(potential_package_id)
                packages_loaded.append(potential_package_id)

            # Remove all packages loaded from the lists to load and update Package statuses and log the changes.
            # Space complexity of O(1) and time complexity of O(n).
            for loaded_id in packages_loaded:
                package = self.packages[loaded_id]
                package.status = PackageStatus.OUT_FOR_DELIVERY
                package.truck_id = truck_id
                self.log_status(loaded_id, package.status)

                package_ids_to_deliver.remove(loaded_id)
                package_ids_to_deliver_by_deadline.remove(loaded_id)

            package_capacity_left -= len(packages_loaded)

        # If any packages were loaded onto the truck calculate the delivery order and send the truck out to deliver
        if len(truck.package_ids) > 0:
            self.__calculate_delivery_order(truck_id, self.location)
            self.trucks[truck_id].depart(self.current_time)

    # Determine and set the delivery order of the packages currently on the truck in-place. The delivery order is
    # formed by a greedily selecting the nearest-neighbor to the current location while taking into account delivery
    # deadline priorities. The next package to deliver will be at the front of the list. Space complexity of
    # O(1) and time complexity of O(n^2).
    def __calculate_delivery_order(self, truck_id: int, current_location: Location) -> None:
        truck = self.trucks[truck_id]
        package_ids = truck.package_ids

        debug("Starting delivery order: " + str(package_ids))
        debug("Total miles: " + str(self.__calculate_total_route_distance(package_ids)))

        for i in range(len(truck.package_ids)):
            min_dist_index = i
            # Everything before 'i' is sorted. Each time we start looking for the closest location to our
            # current location, we set the first index of out unsorted portion as the potential closest location.
            for j in range(i, len(truck.package_ids)):
                delivery_location = self.packages[package_ids[j]].location
                delivery_distance = self.locations[current_location][delivery_location]
                delivery_deadline = self.packages[package_ids[j]].delivery_deadline

                min_dist_location = self.packages[package_ids[min_dist_index]].location
                current_min_distance = self.locations[current_location][min_dist_location]
                current_deadline = self.packages[package_ids[min_dist_index]].delivery_deadline

                # Maintains deadline priorities
                no_deadlines = delivery_deadline == Time(0) and current_deadline == Time(0)
                keep_deadline = delivery_deadline <= current_deadline and delivery_deadline != Time(0)

                # If we find a location closer that does not have a later deadline
                if delivery_distance < current_min_distance and (no_deadlines or keep_deadline):
                    min_dist_index = j

            # Set the closest location found as the new end of our sorted list portion
            temp_id = package_ids[i]
            package_ids[i] = package_ids[min_dist_index]
            package_ids[min_dist_index] = temp_id

            # Set out new current location as the closest location selected
            # and set a new initial min distance index
            current_location = self.packages[package_ids[i]].location

        debug("Ending delivery order: " + str(package_ids))
        debug("Total miles: " + str(self.__calculate_total_route_distance(package_ids)))

    # A quick utility method to determine the total round-trip distance from and to the Hub
    # to deliver a list of packages
    def __calculate_total_route_distance(self, package_ids: List[int]):
        hub_location = self.location
        total_distance = 0.0
        current_location = hub_location

        for package_id in package_ids:
            delivery_location = self.packages[package_id].location
            total_distance += self.locations[current_location][delivery_location]
            current_location = delivery_location

        total_distance += self.locations[current_location][hub_location]

        return total_distance

    # Load location data from csv file into a weighted graph to model the relationship
    # and distance between locations
    def __init_location_data(self) -> None:
        # Dict to temporarily hold distance values to avoid reading the file twice
        distance_matrix = {}
        # Load location data into the Hub
        with open("../resources/wgups_location_data.csv", newline='') as location_data_file:
            reader = csv.reader(location_data_file, delimiter=',')
            # Skip header row
            next(reader, None)
            # For each location add it into the graph as a vertex
            for row in reader:
                new_location = Location(row[2], row[3], row[4], int(row[5]))
                self.locations.insert_vertex(new_location)
                distance_matrix[new_location] = [float(str_value) for str_value in row[6:]]

        # For each location in the graph add in edges with weights as distances to the other
        # locations
        for location, adj_distances in distance_matrix.items():
            for i, adj_location in enumerate(distance_matrix.keys()):
                self.locations.add_edge(location, adj_location, adj_distances[i])

    # Load truck data from csv file into a collection full of Truck objects
    def __init_truck_data(self) -> None:
        # Load package data into the Hub
        with open("../resources/wgups_truck_data.csv", newline='') as truck_data_file:
            reader = csv.reader(truck_data_file, delimiter=',')
            # Skip header row
            next(reader, None)
            # For each package
            for row in reader:
                # Map csv row to array of proper types for easy Truck initialization
                mapped_row: List[Any] = row[:]
                mapped_row[0] = int(mapped_row[0])
                mapped_row[1] = int(mapped_row[1])
                mapped_row[2] = float(mapped_row[2])
                mapped_row[3] = float(mapped_row[3])
                # Create a new truck object with the data
                new_truck = Truck(self, *mapped_row)
                # Store the truck in the Hub to be managed later
                self.trucks.insert(new_truck.id, new_truck)

    # Load package data from csv file into a collection full of Package objects
    def __init_package_data(self) -> None:
        # Load package data into the Hub
        with open("../resources/wgups_package_data.csv", newline='') as package_data_file:
            reader = csv.reader(package_data_file, delimiter=',')
            # Skip header row
            next(reader, None)
            # For each package
            for row in reader:
                # Map csv row to array of proper types for easy Package initialization
                mapped_row: List[Any] = row[:]
                mapped_row[0] = int(mapped_row[0])
                mapped_row[4] = int(mapped_row[4])
                mapped_row[5] = Time(*Time.str_to_time_tuple(mapped_row[5]))
                mapped_row[6] = Time(*Time.str_to_time_tuple(mapped_row[6]))
                mapped_row[7] = float(mapped_row[7])
                mapped_row[8] = str_to_int_or_none(mapped_row[8])
                mapped_row[9] = str_to_int_or_none(mapped_row[9])
                # Create a new package object with the data
                new_package = Package(*mapped_row)
                # Store the package in the Hub for retrieval later
                self.packages.insert(new_package.id, new_package)
