from wgups.time import Time
from wgups.hub import Hub
from wgups.models import Location
from wgups.view import View
from wgups.utilities import parse_user_choice

# Ryan Dorman
# ID: 001002824

if __name__ == "__main__":
    # Initialize WGUPS HUB and start the simulation
    wgups_hub = Hub("WGUPS", Location("4001 South 700 East", "Salt Lake City", "UT", 84107), Time(8))

    # Run the simulation
    wgups_hub.run()

    # Create View to allow easy access to pre-defined ui components
    view = View()

    # Controller logic to allow the user to use the view to query data stored in models
    # associated with the Hub, Truck, and Packages
    while True:
        view.print_logo()
        wgups_hub.print_stats()
        user_choice = parse_user_choice(input(view.main_menu))

        if user_choice == 0:  # Exit
            break
        elif user_choice == 1:  # View Hub info
            view.print_hr()
            time_filter = input(view.time_filter_prompt)

            if parse_user_choice(time_filter) == 0:  # Go back to menu
                continue
            elif Time.is_valid_time_str(time_filter):  # If valid time was entered
                time = Time(*Time.str_to_time_tuple(time_filter))

                if time < wgups_hub.start_time or time > wgups_hub.current_time:
                    print(f">> {time} is not within Today's hours of operation "
                          f"{wgups_hub.start_time} - {wgups_hub.current_time} <<")
                    View.wait_for_keypress()
                    continue

                wgups_hub.print_stats(time)
                View.wait_for_keypress()
            else:
                print(">> Invalid time entered. Ensure format matches HH:MM AM/PM (e.g., 12:24 PM) <<")
                View.wait_for_keypress()

        elif user_choice == 2:  # View Packages info
            view.print_hr()
            time_filter = input(view.time_filter_prompt)

            if parse_user_choice(time_filter) == 0:  # Go back to menu
                continue
            elif Time.is_valid_time_str(time_filter):  # If valid time was entered
                time = Time(*Time.str_to_time_tuple(time_filter))

                if time < wgups_hub.start_time or time > wgups_hub.current_time:
                    print(f">> {time} is not within Today's hours of operation "
                          f"{wgups_hub.start_time} - {wgups_hub.current_time} <<")
                    View.wait_for_keypress()
                    continue

                view.print_hr()
                id_or_all = parse_user_choice(input(view.id_or_all_prompt))

                if id_or_all == 1:  # View all Package info
                    wgups_hub.print_all_packages(time)
                elif id_or_all == 2:  # View Package info by id
                    lookup_id = parse_user_choice(input(f"Enter Package ID to show the Status of at {time}\n> "))

                    if lookup_id in wgups_hub.packages.keys():
                        wgups_hub.print_package_by_id(lookup_id, time)
                    else:
                        print(f">> {lookup_id} is not associated with a Package in the WGUPS system <<")
                else:
                    continue
                View.wait_for_keypress()
            else:
                print(">> Invalid time entered. Ensure format matches HH:MM AM/PM (e.g., 12:24 PM) <<")
                View.wait_for_keypress()

        elif user_choice == 3:  # View Truck info
            view.print_hr()
            time_filter = input(view.time_filter_prompt)

            if parse_user_choice(time_filter) == 0:  # Go back to menu
                continue
            elif Time.is_valid_time_str(time_filter):  # If valid time was entered
                time = Time(*Time.str_to_time_tuple(time_filter))

                if time < wgups_hub.start_time or time > wgups_hub.current_time:
                    print(f">> {time} is not within Today's hours of operation "
                          f"{wgups_hub.start_time} - {wgups_hub.current_time} <<")
                    View.wait_for_keypress()
                    continue

                view.print_hr()
                has_routes = False
                summary_or_detailed = parse_user_choice(input(view.summary_or_detailed_prompt))
                if summary_or_detailed == 2:  # View Truck routes
                    has_routes = True

                view.print_hr()
                id_or_all = parse_user_choice(input(view.id_or_all_prompt))

                if id_or_all == 1:  # View all Trucks info
                    wgups_hub.print_all_trucks(time, has_routes)
                elif id_or_all == 2:  # View Truck info by id
                    lookup_id = parse_user_choice(input(f"Enter Truck ID to show the Status of at {time}\n> "))

                    if lookup_id in wgups_hub.trucks.keys():
                        wgups_hub.print_truck_by_id(lookup_id, time, has_routes)
                    else:
                        print(f">> {lookup_id} is not associated with a Truck in the WGUPS system <<")
                else:
                    continue
                View.wait_for_keypress()
            else:
                print(">> Invalid time entered. Ensure format matches HH:MM AM/PM (e.g., 12:24 PM) <<")
                View.wait_for_keypress()
                continue
        else:
            continue
