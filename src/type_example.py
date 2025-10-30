from typing import Any, Callable


def main(processor: Callable[[Any], list[int]]) -> None:
    data = [1, 2, 3, None, 4, 5, None, 6]
    processed_data = processor(data)
    print(processed_data)
    
    
    def process_data(data: list[int | None]) -> list[int]:
        result = []
        for item in data:
            if item is not None:
                result.append(item * 2)
        return result
    
    
    # process_data(...)
    
    print(process_data([5, 15, 25, 3, 8, 12]))
    
    print(process_data([5, 15, 25, 3, 8, 12]))
    
    
    A = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],          
    ]
    
    B = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],          
    ]
    # print(process_data(["1", "2", "3", "5", "4"]))
