# System-ekspertowy
System oceny przydatności pytań na podstawie ich treści dla portalu StackOverflow

## Dane
Link: https://www.kaggle.com/imoore/60k-stack-overflow-questions-with-quality-rate
(kopia zrobiona w katalogu 'resources' z dodatkowym plikiem "sample.csv", który jest fragmentem "training.csv")
trzeba rozpakować do folderu 'code', aby zadziałało bez modyfikacji

## Kod
W katalogu 'code' znajduje się działający szablon kodu, który myślę, że sprawdzi się w dalszej części.
main.py - tu wrzucamy metody potrzebne do zarządzania systemem, ale niezależne od danych
utility.py - zawiera przydatne funkcje dla evaluator.py
evaluator.py - metody używane do 'rozpakowania' wiersza csv na dane i przydzielenia do konkretnej kategorii

## Wyniki
Najlepszy wynik 74.31