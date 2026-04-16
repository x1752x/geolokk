class Detector:
    """
    Реализация алгоритма STA/LTA
    """

    n_sta: int  # Длина короткого окна
    n_lta: int  # Длина длинного окна
    treshold: float  # Пороговое значение STA/LTA (ratio)
    sta: float | None = None  # Скользящее среднее для STA
    lta: float | None = None  # Скользящее среднее для LTA
    is_active: bool = False  # Атрибут для хранения состояния

    def __init__(self, n_sta: int, n_lta: int, treshold: float):
        self.n_sta = n_sta
        self.n_lta = n_lta
        self.treshold = treshold
        self.is_active = False  # Инициализируем состояние

    def detect(self, x: float) -> bool:
        abs_x = abs(x)

        # Инициализация STA и LTA при первом запуске
        if self.sta is None or self.lta is None:
            self.sta = abs_x
            self.lta = abs_x
            # При инициализации событие не считаем начавшимся, 
            # если только начальное значение уже не аномально высокое, 
            # но обычно начинают с False.
            return False 
        
        # Обновление STA и LTA (экспоненциальное скользящее среднее)
        self.sta = self.sta + (abs_x - self.sta) / self.n_sta
        self.lta = self.lta + (abs_x - self.lta) / self.n_lta
        
        # Защита от деления на ноль
        ratio = self.sta / self.lta if self.lta != 0 else 0
        
        # Логика определения фронта и спада
        if ratio >= self.treshold:
            if not self.is_active:
                # Событие НАЧАЛОСЬ (переход из False в True)
                self.is_active = True
                return True
            else:
                # Событие продолжается, ничего не возвращаем (или False)
                return False
                
        else: # ratio < self.treshold
            if self.is_active:
                # Событие ЗАКОНЧИЛОСЬ (переход из True в False)
                self.is_active = False
                return False
            else:
                # Тишина
                return False