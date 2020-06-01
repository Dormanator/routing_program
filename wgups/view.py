# Wrapper class for main components of view
class View:
    def __init__(self):
        self.__init_data()

    def print_logo(self) -> None:
        print(self.logo)

    def print_hr(self):
        print(self.horizontal_rule)

    @staticmethod
    def wait_for_keypress() -> None:
        input("Press any key to return to the Menu\n> ")

    def __init_data(self):
        with open('../resources/view.txt', 'r') as file:
            data = file.read().split(',')
            self.logo = data[0]
            self.main_menu = data[1]
            self.time_filter_prompt = data[2]
            self.id_or_all_prompt = data[3]
            self.horizontal_rule = data[4]
            self.summary_or_detailed_prompt = data[5]
