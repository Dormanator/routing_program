Ryan Dorman

ID: 001002824

# **WGUPS Routing Program**

## **I. Problem**

The Western Governors University Parcel Service (WGUPS) is unable to ensure all their packages are being delivered on time. A program must be developed to determine efficient delivery routes to ensure their packages are delivered by their promised deadlines.

#### Resources

- A matrix of delivery locations with their distances to each other
- A list of packages with delivery locations, delivery deadlines, and special notes

#### Assumptions

- Each truck can carry a maximum of 16 packages.
- Trucks travel at an average speed of 18 miles per hour.
- Trucks have a &quot;infinite amount of gas&quot; with no need to stop.
- Each driver stays with the same truck as long as that truck is in service.
- Drivers leave the hub at 8:00 a.m., with the truck loaded, and can return to the hub for packages if needed. The day ends when all 40 packages have been delivered.
- Delivery time is instantaneous, i.e., no time passes while at a delivery (that time is factored into the average speed of the trucks).
- There is up to one special note for each package.
- The wrong delivery address for package #9, Third District Juvenile Court, will be corrected at 10:20 a.m. The correct address is 410 S State St., Salt Lake City, UT 84111.
- The package ID is unique; there are no collisions.
- No further assumptions exist or are allowed.

## **II. Solution**

### A. Overview

The solution uses a hash table to store the package and truck data and a graph structure to store the delivery locations and their distances. It uses a greedy heuristic algorithm to determine which packages need to go out for delivery, and the route to take when delivering them.

In the simulation with the provided data, the implementation of this algorithm resulted in all 40 packages being delivered on-time. The following screenshots provide a summary of the simulation&#39;s results.

#### Entire day:

![Logs for entire day](resources/entire_day_log.png)

#### 8:45 AM:

![Logs for 8:45 AM](resources/8_45_AM_log.png)

#### 10:00 AM:

![Logs for 10:00 AM](resources/10_00_AM_log.png)

#### 12:30 PM:

![Logs for 12:30 AM](resources/12_30_PM_log.png)

### B. Data Structures

The WGUPS routing program was built using two core data structure types. A graph to handle the location and distance data, and a hash table to store the packages and trucks.

#### Adjacency Matrix Graph

Each delivery location in the program is stored in the graph as a vertex. The graph uses an adjacency matrix to store distances between each of the locations as edge weights between the graph&#39;s vertices. An adjacency matrix design was chosen for the graph since the location data includes distances from each location to every other location. In other words, our graph does not have sparse edge but instead has edges from every vertex to every other vertex. This means we have no empty space being wasted in our matrix. Due its basis on a matrix, the space complexity of the graph is O(n2) since for every location (n) we store the distance to every location (n).

Inserting a vertex into the graph has a space complexity of O(1) and a time complexity of O(n). Removing a vertex from the graph has a space and time complexity of O(1). Adding an edge between two vertices has a space and time complexity of O(1). Each vertex stored in the graph is associated with a unique key made up by hashing the location data. As a result, graph lookups to retrieve the weight between two vertices, or in our case to discover the distance between two locations, are associated with a space and time complexity of O(1).

#### Chaining Hash Table

The hash table using chaining stores the data for all packages and all trucks in the program, in separate collections. These data points are stored as key-value pairs with the unique id of a package or truck being stored as the key and the data associated with it as the value . This ensures easy look-up of all the data associated with a package or truck by their unique ids.

A single insert function takes both the key and associated value to be stored in the hash table. The keys associated with each value must be unique because if a key already exists in the hash table the insert function will update the value for the existing key. If a key-value pair is being inserted or updated the space complexity is O(1) and in most cases the time complexity is O(1). When the hash table&#39;s insertion function will store a new key-value pair that will result it half of its capacity being used, the hash table will double in size and re-hash each item already stored in the table. When an insertion occurs, and a re-size is needed the space and time complexities becomes O(n) in this worst-case scenario. Searching and removing for key-value pairs in the hash table are done by passing in the associated key and each returns the value that was searched for or removed depending on the function. Both search and remove have a space complexity of (1) and a time complexity of O(1) on average and O(n) in the worst-case.

#### Strengths and Scale

Strengths of this hash table design are the way it handles and avoids collisions. One way the hash table handles key collisions is via chaining. This means each storage point, or bucket, in the hash table is a list that can store multiple key-value pairs when the hashed keys indicate the values should be stored in the same bucket. Additionally, the hash table ensures no more than half of its buckets are storing values at any given time. This increases the number of buckets key-value pairs can end up in, which greatly reduces the likelihood of collisions occurring in the first place.

As WGUPS scales and handles more packages and trucks, there will continue to be a low chance for collisions due to these strengths. Since each key will be associated with a unique bucket that can be located at a constant speed on average, continued speed for hash table interactions at scale are expected. At scale, the resize capabilities of the hash table will ensure it grows to store an increased number of packages and while resizing will require O(n) time when it occurs, it will not occur frequently.

#### Alternate Data Structures

Another type of hash table could have been used that takes another approach to handling collisions. For example, a hash table that uses linear probing rather than chaining could have been used. The chaining implementation has a list at each bucket to store any values with keys that collide. With linear probing, when a collision occurs the new value is simply stored in the next empty bucket (Lysecky &amp; Vahid, 2013). One downside of the linear probing implementation is if collisions occur values can end up being stored in buckets that are far away from the indices their respective keys hash to. Since the values would not be stored where the hash table expects to find them, it can make insertions, removals, and searches take O(n) time. With chaining, when collisions occur values are still stored at the bucket index given by the hashed key. The values are simply added to a list or &#39;chain&#39; that must be searched if more than one value is in it (Lysecky &amp; Vahid, 2013). Ultimately, the chaining implementation is likely to take less time that linear probing when executing methods such as insertions and searches. This is because the cases that would take O(n) time with chaining would only occur if every key resulted in the same hash and one bucket&#39;s chain stored all values.

A linked-list is another data structure that could have been used to store the packages and trucks. A linked list is essentially a series of nodes that store data, like the package data, but also contain references to the memory location of the next node in the list (Lysecky &amp; Vahid, 2013). Like a hash table, linked-lists support dynamic resizing and can grow as their number of elements increases. However, a linked list will grow one element at a time as a new value is added to it. This means that the resize function of a linked list will have a time complexity of O(1) if the new value is inserted at the end of the list. A linked list does not store values with an associated key to allow lookups in the list at constant time. As a result, searching for values in the linked list has a time complexity of O(n) and finding packages by id would require a search that checks the values at each node of the list. This also means that insertions into the list at a specific location can take O(n) as the list must iterate to that location for the insertion to occur. The linked list offers more efficient capabilities for resizing as packages are added to the end of the list when compared to the chaining hash table. On the other hand, performing searches for packages or insertions in the middle or end of the linked list will take O(n) time resulting in worse performance than the hash table on average.

### C. Algorithm

To determine the optimal delivery routes, first, the packages that will go out for delivery must be selected and loaded onto the truck. Then, the optimal route the packages should be delivered in is determined by greedily selecting the closest location to visit next and arranging the packages loaded on the truck in this order.

The pseudo code for the algorithm is:
```
# 1) Prioritize packages and load them on truck

# a)

truck := getTruckToBeLoaded()

package_ids_to_deliver := getPackageIdsReadyForDelivery()

# b)

prioritizeForLoading(package_ids_to_deliver)

# c)

loadPackages(truck, package_ids_to_deliver)

# 2) Determine delivery order for packages loaded

# a)

current_location := getLocation(WGUPS Hub)

number_packages_loaded := length(truck.packages_loaded)

package_id_w_closest_location := None

# b)

for each package_id in truck.packages_loaded:

for unordered_package_id in truck.packages_loaded:

if unordered_package_id is closer than package_id to current_location:

package_id_w_closest_location = unordered_package_id

# c)

if package_id delivery_deadline not earlier than package_id_w_closest_location:

swap package_id_w_closest_location with package_id

current_location = getLocation(package_id_w_closest_location)
```
The algorithm is composed of several core steps, notated in the pseudo code, which are examined in detail below:

1. Prioritize packages and load them on truck.

    a. Get the truck we are loading and determining a route for. Since the trucks are stored in the hash table this lookup has a space complexity O(1) and time complexity of O(1). Then, we get a list of packages id for packages ready for delivery on this truck. The package ids returned will be at the Hub and ready to go out for delivery. The ids will not be associated with packages pre-assigned to another truck or be associated with a group of packages where one is pre-assigned to another truck. The filtering that takes place to achieve the correct list of package ids has space and time complexities of O(1) and O(n).

    b. Prioritize the package ids by packages with the same delivery location and then by those that have been pre-assigned to be delivered on this truck based on their notes. This initial prioritization has a space and time complexity of O(n) and O(nlogn) (Timsort, 2020). The package ids are then sorted by their packages&#39; delivery deadlines. Deadline prioritization has a space complexity of O(n) and time complexity of O(nlogn) (Timsort, 2020).

    c. While there is empty space in the truck and packages to deliver, the package with the highest priority is selected. It is determined if the package belong to a group of packages that must be delivered together based on their notes. If so, it makes sure all group members can fit on the truck and loads them if they can. If there is no group associated with the package it simply loads it onto the truck. The loading process has a space and time complexity of O(1) and O(n).

2. Determine delivery order for packages loaded.
    
    a. Initialize variables that tell us where the route needs to start from, how many packages are being routed, and one to hold the package id for the closet delivery location found. These initializations have a space and time complexity of O(1).

    b. Work our way from the first element of the list of package ids loaded on the truck to the last, putting the left side in sorted order until the entire list is sorted. We check the distance of each delivery location from our current location and store the package id associated with the closest location for each iteration. Comparing each location against every other location, even when not rechecking the sorted section, has a space complexity of O(n2) locations and a time complexity of O(n2) packages.

    c. At the end of each iteration, we determine if the current unsorted package id we compared against others has an earlier delivery deadline. If the current package has a closer deadline, we do not swap it with the one with a closer location and we consider it sorted. If it has a later or no deadline, then it is swapped with the package id the has a closer delivery location and we move our iterator to the next unsort package id. We then set the current location to the location of the last sorted package id so we can determine in the next iteration what the next optimal delivery location is. These priority checks and variable updates occur each iteration and have a space and time complexity of O(1).

#### Strengths and Scale

One strength of this routing program is the space it requires to run. The storage of package data in a hash table at the Hub allows it and trucks to easily get any package information needed via table lookups by package id. This reduces the need for all package details to be stored multiple times within the Hub&#39;s system or on computer systems within the trucks redundantly. Instead, within the system packages are referenced and communicated by their unique id numbers which can be used to look up their actual data in the table as needed. This will ensure as the system scales and more packages and trucks are added the space requirements for each addition will be constant in nature as each new item will not ever be stored fully in multiple places but will be stored in the table once and referenced throughout the system by its id. With the Hub as the central data repository, it also ensures it is aware of any updates to package deadlines and locations. This means if the delivery addresses or deadlines of any package changes while the truck is in route, the Hub will be aware of the changes within its system and the delivery route can be re-calculated based on the truck&#39;s current location and the updated package data and communicated to the truck while it is in route.

Another strength of this algorithm is the time required to run it. This solution does not attempt to explore every potential combination of packages that could be loaded onto the truck or check every route delivery route possible. Instead, it takes an imperfect heuristic approach that prioritizes the aspects of packages most important to our problem such as delivery deadlines, packages that must be delivered together, and trucks packages must be delivered on over the potential smallest delivery routes. This ensures the core problem facing WGUPS, which is inconsistent deliveries and late delivers, is put first and then we determine a delivery route with the packages selected. For the delivery route we take a nearest-neighbor approach that only considers what the next closest locations will be, rather than exploring all potential routes to truly find the one with the minimum delivery distance. The solution takes these shortcuts to guarantee packages can be routed quickly even at scale. As more packages and trucks are added to the system relying on this greedy heuristic will ensure packages can still be routed quickly while still maintaining the core goals of the system.

#### Alternate Algorithms

One algorithm that could have been used to solve the problem is a brute force algorithm (Traveling Salesman Problem, 2020). Rather than attempting to find a workable solution that is not completely optimal, like a heuristic algorithm, a brute force approach would try every possible routing combination to find the best possible solution. Although discovering the most optimal route for every delivery situation would be ideal, the space and time complexity of this approach is O(nlogn) and O(n!) (Traveling Salesman Problem, 2020). With its time complexity growing factorially, this algorithm would take much too long to solve as WGUPS scales and the calculation of routes for more packages and trucks are necessary.

Another algorithm that could be used is a heuristic algorithm that focuses on route improvement (Nilsson, 2003). This approach would ensure scalability and be similar initially to our current solution, but after a route is determined using nearest-neighbor selection we determine if it can be improved at all. This can be done by selecting a sub-route of our package ids sorted in delivery order and removing it from our route to give us two smaller routes. We then determine if we can reconnect these routes in another way to obtain a route with a smaller distance than our original. If our new route is smaller than the original than we keep it, if not than we keep our original route. This is done until all possible sub-routes of two and their potential rearrangements are explored. This additional route improvement results in a time and space complexity of O(n2) and O(n4) (Nilsson, 2003).

### D. Time and Space Complexity

When considering the space and time complexity values that make up the solution&#39;s data structures and algorithms, presented in the above sections, an approximation of the space and time complexity for the entire program can be derived.

| _**Algorithm Component**_ | **Time Complexity** | **Space Complexity** |
| --- | --- | --- |
| _**1.a**_ | O(O(1) + O(n)) = **O(n)** | O(O(1) + O(1)) = **O(1)** |
| _**1.b**_ | O(2 * O(nlogn)) = **O(nlogn)****)**| O(2 * O(n)) =**O(n)****)** |
| _**1.c**_ | **O(n)** | **O(1)** |
| _**2.a**_ | **O(1)** | **O(1)** |
| _**2.b**_ | **O(n**<sup>**2**</sup>**)** | **O(n**<sup>**2**</sup>**)** |
| _**2.c**_ | **O(1)** | **O(1)** |
| | **+** | **+** |
| _**Totals:**_ | **O(n**<sup>**2**</sup> **+ nlogn + n)** | **O(n**<sup>**2**</sup> **+ n)** |
|  |  |  |

## **IV. What I Would Change**

One aspect I would improve is not related to the solution&#39;s design, but how it was implemented with Python. After finishing the project, I learned about the Python Data Classes module which helps simplify objected-oriented programing in Python for classes intended to hold data. Considering the solution is highly based on classes that hold data, use of this module could help reinforce the object-oriented design I had in mind for the solution. This module allows the use annotations which enable the reduction of boilerplate code when creating classes such as parameter to object property mapping that occurs in constructors and provide helpful implementation of class level methods. All these features would help simplify the solution and improve its readability.

Another aspect I would change is how the core route finding algorithm is implemented. I would like to explore improving the total miles traveled by the trucks used in the solution while maintaining on-time deliveries. I think the easiest way to allow for such improvements would be to use a route optimization technique. Such optimizations could be done by exploring whether smaller routes within the nearest neighbor solution discussed and attempting to create new routes out of them that reduce the total miles of the route. This sort of alternate algorithm is discussed further in the subsection _Alternate_ Algorithms in Section V. I think it would be interesting to explore these types of route improvements and see whether they warrant the additional time complexity they introduce into the solution based on the level of route optimization actually gained from their implementation.

## **VI. Sources**

Timsort. (2020). En.wikipedia.org. Available at: [en.wikipedia.org/wiki/Timsort](https://en.wikipedia.org/wiki/Timsort)

Traveling Salesman Problem. (2020). En.wikipedia.org. Available at: [en.wikipedia.org/wiki/Travelling\_salesman\_problem](https://en.wikipedia.org/wiki/Travelling_salesman_problem)

Lysecky, R., &amp; Vahid, F. (2018). C950: Data Structures and Algorithms Ii. zyBook.

Nilsson, C. (2003). Heuristics for the traveling salesman problem. Linkoping University.