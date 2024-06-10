class Car:
    def __init__(self, car):
        self.name = car
        self.water = 0
        self.foam = 0
        self.fire_car = 0
        self.kombat = 0
        self.police_car = 0
        self.swat = 0
        self.cargo()

    def cargo(self):
        match self.name:
            case "ПСА":
                self.water = 3000
                self.foam = 500
                self.fire_car = 1
            case 'АЦЛ':
                self.fire_car = 1
            case 'ПКП':
                self.kombat = 1
            case 'АЦ-3,0-40':
                self.water = 3000
                self.foam = 500
            case 'АЦ 2,3-40':
                self.water = 1500
                self.foam = 250
            case 'АЦ-9,4-60':
                self.water = 6000
            case 'Пожарный автомобиль пенного тушения':
                self.foam = 3000
            case 'Автомобиль с полицейской собакой':
                self.police_car = 1
            case 'Бронемашина спецназа':
                self.swat = 6
            case 'Внедорожник спецназа':
                self.swat = 4
