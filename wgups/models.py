from enum import Enum
from typing import List
from wgups.time import Time
from wgups.utilities import debug
import copy


# Model to contain and communicate location data
class Location:
    def __init__(self, address: str, city: str, state: str, zip_code: int):
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code

    def key(self):
        return self.address, self.city, self.state, self.zip_code

    def __copy__(self):
        return Location(*self.key())

    def __hash__(self) -> int:
        return hash(self.key())

    def __eq__(self, other_location):
        if isinstance(other_location, Location):
            return self.key() == other_location.key()
        return NotImplemented

    def __str__(self):
        return f"{self.address}\n\t{self.city}, {self.state} {self.zip_code}\n"


# Enum for representing package status
class PackageStatus(Enum):
    PENDING = 0,
    READY_FOR_PICKUP = 1,
    OUT_FOR_DELIVERY = 2,
    DELIVERED = 3,
    DELIVERED_LATE = 4


# Used to maintain structure for the history of a package so we can later
# lookup a Package's status for any time throughout the day.
class PackageStatusLog:
    def __init__(self, status: PackageStatus, start_time: Time):
        self.status = status
        self.start_time = start_time
        self.end_time = Time()

    def __str__(self):
        return ''.join([f"Status: {self.status.name}\n",
                        f"Start Time: {self.start_time}\n",
                        f"End Time: {self.end_time}"])


# Model to contain and communicate package data
class Package:
    def __init__(self, package_id: int, address: str, city: str, state: str, zip_code: int,
                 arrival_time: Time, delivery_deadline: Time,
                 mass_kilo: float, truck_id: int, group_id: int, note: str):
        self.id = package_id
        self.location = Location(address, city, state, zip_code)
        self.arrival_time = arrival_time
        self.delivery_deadline = delivery_deadline
        self.mass_kilo = mass_kilo
        self.truck_id = truck_id
        self.group_id = group_id
        self.note = note
        self.status = PackageStatus.PENDING

    # Two packages are equal if they have the same id
    def __eq__(self, other_package):
        return self.id == other_package.id

    # Allows easy copy of package values
    def __copy__(self):
        return Package(self.id, *self.location.key(), self.arrival_time, self.delivery_deadline, self.mass_kilo,
                       self.truck_id, self.group_id, self.note)

    # Convenience method for translating model to string
    def __str__(self):
        return ''.join([f"Package ID: {self.id}\t\tStatus: {self.status.name}\n",
                        f"\nPick-up at: {self.arrival_time}\n",
                        f"Deliver by: {self.delivery_deadline}\n\n",
                        f"Delivery Address:\n\t{self.location}\n",
                        f"Note: {self.note}\n",
                        f"Weight: {self.mass_kilo} kilograms\n",
                        f"Delivery Group ID: {self.group_id}\n",
                        f"Assigned Truck ID: {self.truck_id}"])


# Enum representing truck status
class TruckStatus(Enum):
    AT_HUB = 0,
    OUT_FOR_DELIVERIES = 1


# Used to maintain structure for the history of a truck so we can later
# lookup a Truck's status for any time throughout the day.
class TruckStatusLog:
    def __init__(self, status: TruckStatus, miles_traveled: int, route_traveled: List[Location],
                 next_destination: Location, arrival_time: Time, start_time: Time):
        self.status = status
        self.miles_traveled = miles_traveled
        self.route_traveled = route_traveled
        self.next_destination = next_destination
        self.arrival_time = arrival_time
        self.start_time = start_time
        self.end_time = Time()

    def __str__(self):
        return ''.join([f"Status: {self.status.name}\n",
                        f"Start Time: {self.start_time}\n",
                        f"End Time: {self.end_time}\n\n",
                        f"Next Destination: {self.next_destination}\n",
                        f"Arrival Time: {self.arrival_time}\n",
                        f"Miles traveled: {self.miles_traveled}"])


# Model to contain and communicate truck data
class Truck:
    def __init__(self, hub: "Hub", truck_id: int, package_capacity: int, avg_speed_mph: float,
                 delivery_time_min: float):
        self.hub = hub
        self.id = truck_id
        self.package_capacity = package_capacity
        self.avg_speed_mph = avg_speed_mph
        self.delivery_time_min = delivery_time_min
        self.total_miles_traveled = 0.0
        self.route_traveled = []
        self.status = TruckStatus.AT_HUB
        self.package_ids = []
        self.next_destination = None
        self.arrival_time = None

        self.hub.log_status(self.id, self.status, self.total_miles_traveled, self.route_traveled,
                            self.next_destination, self.arrival_time)

    def depart(self, current_time: Time) -> None:
        self.status = TruckStatus.OUT_FOR_DELIVERIES
        self.next_destination = self.hub.location
        self.__set_next_delivery_destination(current_time)

        debug("Departing Hub")
        debug(str(self))

    def dock_at_hub(self) -> None:
        self.status = TruckStatus.AT_HUB
        self.__update_miles_traveled(self.next_destination)
        self.next_destination = None

        self.hub.log_status(self.id, self.status, self.total_miles_traveled, self.route_traveled,
                            self.next_destination, self.arrival_time)

        debug("Docking at Hub")
        debug(str(self))

    def update_state(self, current_time: Time) -> None:
        # If at Hub wait
        if self.status is TruckStatus.AT_HUB:
            return
        # If out for deliveries
        if self.status is TruckStatus.OUT_FOR_DELIVERIES and self.next_destination is not None:
            # If next destination set and the arrival time hasn't occurred, wait
            if self.arrival_time > current_time:
                return
            # Else we have arrived
            else:
                # update package status, log package change, and pop id off package_ids
                debug(f"Delivering Package {self.package_ids[0]} at {current_time}")
                package_id_to_deliver = self.package_ids.pop(0)
                package_to_deliver = self.hub.packages[package_id_to_deliver]
                delivery_deadline = package_to_deliver.delivery_deadline

                # Determine if the delivery is on time or late
                if delivery_deadline != Time(0) and delivery_deadline < current_time:
                    package_to_deliver.status = PackageStatus.DELIVERED_LATE
                else:
                    package_to_deliver.status = PackageStatus.DELIVERED

                self.hub.log_status(package_to_deliver.id, package_to_deliver.status)

                # If packages set the next destination and arrival time
                if len(self.package_ids) > 0:
                    self.__set_next_delivery_destination(current_time)
                # If out of packages set next destination as Hub
                else:
                    self.__return_to_hub(current_time)

    def __set_next_delivery_destination(self, current_time: Time):
        # Find the next package and its destination
        next_package = self.hub.packages[self.package_ids[0]]
        # Using the location we are about to replace, because we are at it, we determine
        # the distance and time to travel
        next_destination = next_package.location
        current_location = self.next_destination
        self.__set_distance_and_arrival(current_location, next_destination, current_time)
        self.next_destination = next_destination

    def __return_to_hub(self, current_time: Time):
        next_destination = self.hub.location
        current_location = self.next_destination  # we just arrived here and will update this next
        self.__set_distance_and_arrival(current_location, next_destination, current_time)
        self.next_destination = next_destination

    def __set_distance_and_arrival(self, current_location: Location, next_destination: Location, current_time: Time):
        # Determine arrival time based on distance and truck speed and set it
        miles_to_travel = self.hub.locations[current_location][next_destination]
        debug(40 * '=')
        debug(f"Current location:\n {current_location}")
        debug(f"Next Destination:\n {next_destination}")
        # miles / mph * min_in_hour = min to travel
        time_to_travel_in_min = int(miles_to_travel / self.avg_speed_mph * 60)
        debug(miles_to_travel)
        debug(self.avg_speed_mph)
        debug(f"Time to travel calculated: {time_to_travel_in_min}")
        arrival_time = copy.copy(current_time)
        arrival_time.add_minutes(time_to_travel_in_min)
        # Set new values and log updates
        self.arrival_time = arrival_time
        debug(f"Arrival time set: {self.arrival_time}")
        self.__update_miles_traveled(current_location)
        self.hub.log_status(self.id, self.status, self.total_miles_traveled, self.route_traveled,
                            next_destination, self.arrival_time)

    def __update_miles_traveled(self, current_location: Location):
        # Update distance traveled by adding the distance from our last location to our current
        if len(self.route_traveled) > 0 and current_location != self.route_traveled[-1]:
            miles_traveled = self.hub.locations[self.route_traveled[-1]][current_location]
            debug(f"Miles traveled: {miles_traveled}")
            self.total_miles_traveled += miles_traveled
            self.route_traveled.append(current_location)
        elif len(self.route_traveled) == 0:
            self.route_traveled.append(current_location)

    def __str__(self):
        return ''.join([f"Truck ID: {self.id}\t\tStatus: {self.status.name or 'None'}\n",
                        f"Total Miles: {self.total_miles_traveled}\n",
                        f"Next Destination: {self.next_destination}\n",
                        f"Arrival Time: {self.arrival_time}\n",
                        f"Packages to deliver: {len(self.package_ids)}"])
