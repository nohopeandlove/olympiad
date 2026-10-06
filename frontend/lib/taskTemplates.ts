export type TaskTemplate = {id:string;title:string;statement:string;input_description:string;output_description:string;constraints:string;difficulty:string;points:number;time_limit:number;memory_limit:number;tests:{input:string;expected:string;public:boolean}[]};
export const spaceTasks: TaskTemplate[] = [
  {
    "id": "1",
    "title": "Тайное послание звёзд",
    "statement": "Ты получил сигнал от звёзд: «Я звёздный путешественник!». Выведи это послание, чтобы начать приключение.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Ввод не требуется.",
    "output_description": "Я звёздный путешественник!",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "",
        "expected": "Я звёздный путешественник!",
        "public": true
      }
    ]
  },
  {
    "id": "2",
    "title": "Звёздная энергия для прыжка",
    "statement": "Корабль готовится к гиперпрыжку! Сложи энергию двух звёзд.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Два целых числа через пробел, каждое от −1000000 до 1000000.",
    "output_description": "Сумма двух чисел.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "4 5",
        "expected": "9",
        "public": true
      },
      {
        "input": "0 0",
        "expected": "0",
        "public": false
      },
      {
        "input": "-8 3",
        "expected": "-5",
        "public": false
      },
      {
        "input": "1000000 1000000",
        "expected": "2000000",
        "public": false
      }
    ]
  },
  {
    "id": "3",
    "title": "Соревнование космических дронов",
    "statement": "Сравни скорости двух дронов и сообщи, какой быстрее или что скорости одинаковы.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Две целочисленные скорости через пробел: от 0 до 1000000.",
    "output_description": "Первый дрон быстрее / Второй дрон быстрее / Дроны одинаковы.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "7 5",
        "expected": "Первый дрон быстрее",
        "public": true
      },
      {
        "input": "3 10",
        "expected": "Второй дрон быстрее",
        "public": true
      },
      {
        "input": "8 8",
        "expected": "Дроны одинаковы",
        "public": true
      },
      {
        "input": "0 0",
        "expected": "Дроны одинаковы",
        "public": false
      },
      {
        "input": "0 1",
        "expected": "Второй дрон быстрее",
        "public": false
      },
      {
        "input": "1000000 0",
        "expected": "Первый дрон быстрее",
        "public": false
      }
    ]
  },
  {
    "id": "4",
    "title": "Сияние кристалла",
    "statement": "Кристалл сияет, если его яркость больше нуля. Определи, сияет ли он.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одно целое число от −1000000 до 1000000.",
    "output_description": "Да, если число больше нуля; иначе Нет.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "7",
        "expected": "Да",
        "public": true
      },
      {
        "input": "-3",
        "expected": "Нет",
        "public": true
      },
      {
        "input": "0",
        "expected": "Нет",
        "public": true
      },
      {
        "input": "1",
        "expected": "Да",
        "public": false
      },
      {
        "input": "-1",
        "expected": "Нет",
        "public": false
      }
    ]
  },
  {
    "id": "5",
    "title": "Запуск ракеты: обратный отсчёт",
    "statement": "Подготовь ракету к запуску: выведи обратный отсчёт от 5 до 1.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Ввод не требуется.",
    "output_description": "Числа 5 4 3 2 1 через пробел.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "",
        "expected": "5 4 3 2 1",
        "public": true
      }
    ]
  },
  {
    "id": "6",
    "title": "Путь к тайной планете",
    "statement": "Проложи маршрут к секретной планете: выведи числа от 1 до N включительно.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Целое число N от 1 до 1000.",
    "output_description": "Числа от 1 до N через пробел.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "4",
        "expected": "1 2 3 4",
        "public": true
      },
      {
        "input": "1",
        "expected": "1",
        "public": false
      },
      {
        "input": "10",
        "expected": "1 2 3 4 5 6 7 8 9 10",
        "public": false
      },
      {
        "input": "1000",
        "expected": "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 256 257 258 259 260 261 262 263 264 265 266 267 268 269 270 271 272 273 274 275 276 277 278 279 280 281 282 283 284 285 286 287 288 289 290 291 292 293 294 295 296 297 298 299 300 301 302 303 304 305 306 307 308 309 310 311 312 313 314 315 316 317 318 319 320 321 322 323 324 325 326 327 328 329 330 331 332 333 334 335 336 337 338 339 340 341 342 343 344 345 346 347 348 349 350 351 352 353 354 355 356 357 358 359 360 361 362 363 364 365 366 367 368 369 370 371 372 373 374 375 376 377 378 379 380 381 382 383 384 385 386 387 388 389 390 391 392 393 394 395 396 397 398 399 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 418 419 420 421 422 423 424 425 426 427 428 429 430 431 432 433 434 435 436 437 438 439 440 441 442 443 444 445 446 447 448 449 450 451 452 453 454 455 456 457 458 459 460 461 462 463 464 465 466 467 468 469 470 471 472 473 474 475 476 477 478 479 480 481 482 483 484 485 486 487 488 489 490 491 492 493 494 495 496 497 498 499 500 501 502 503 504 505 506 507 508 509 510 511 512 513 514 515 516 517 518 519 520 521 522 523 524 525 526 527 528 529 530 531 532 533 534 535 536 537 538 539 540 541 542 543 544 545 546 547 548 549 550 551 552 553 554 555 556 557 558 559 560 561 562 563 564 565 566 567 568 569 570 571 572 573 574 575 576 577 578 579 580 581 582 583 584 585 586 587 588 589 590 591 592 593 594 595 596 597 598 599 600 601 602 603 604 605 606 607 608 609 610 611 612 613 614 615 616 617 618 619 620 621 622 623 624 625 626 627 628 629 630 631 632 633 634 635 636 637 638 639 640 641 642 643 644 645 646 647 648 649 650 651 652 653 654 655 656 657 658 659 660 661 662 663 664 665 666 667 668 669 670 671 672 673 674 675 676 677 678 679 680 681 682 683 684 685 686 687 688 689 690 691 692 693 694 695 696 697 698 699 700 701 702 703 704 705 706 707 708 709 710 711 712 713 714 715 716 717 718 719 720 721 722 723 724 725 726 727 728 729 730 731 732 733 734 735 736 737 738 739 740 741 742 743 744 745 746 747 748 749 750 751 752 753 754 755 756 757 758 759 760 761 762 763 764 765 766 767 768 769 770 771 772 773 774 775 776 777 778 779 780 781 782 783 784 785 786 787 788 789 790 791 792 793 794 795 796 797 798 799 800 801 802 803 804 805 806 807 808 809 810 811 812 813 814 815 816 817 818 819 820 821 822 823 824 825 826 827 828 829 830 831 832 833 834 835 836 837 838 839 840 841 842 843 844 845 846 847 848 849 850 851 852 853 854 855 856 857 858 859 860 861 862 863 864 865 866 867 868 869 870 871 872 873 874 875 876 877 878 879 880 881 882 883 884 885 886 887 888 889 890 891 892 893 894 895 896 897 898 899 900 901 902 903 904 905 906 907 908 909 910 911 912 913 914 915 916 917 918 919 920 921 922 923 924 925 926 927 928 929 930 931 932 933 934 935 936 937 938 939 940 941 942 943 944 945 946 947 948 949 950 951 952 953 954 955 956 957 958 959 960 961 962 963 964 965 966 967 968 969 970 971 972 973 974 975 976 977 978 979 980 981 982 983 984 985 986 987 988 989 990 991 992 993 994 995 996 997 998 999 1000",
        "public": false
      }
    ]
  },
  {
    "id": "7",
    "title": "Сокровища астероида",
    "statement": "Создай список чисел 1, 2, 3, 4, 5 — количества кристаллов в сокровищах — и выведи его.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Ввод не требуется.",
    "output_description": "[1, 2, 3, 4, 5]",
    "constraints": "Используй список. Наличие списка в коде проверяет преподаватель.",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "",
        "expected": "[1, 2, 3, 4, 5]",
        "public": true
      }
    ]
  },
  {
    "id": "8",
    "title": "Первый кристалл сокровища",
    "statement": "Считай список чисел — кристаллов астероида — и выведи первый элемент.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "От 1 до 100 целых чисел через пробел; каждое от −1000000 до 1000000.",
    "output_description": "Первое число.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "3 5 7 2",
        "expected": "3",
        "public": true
      },
      {
        "input": "42",
        "expected": "42",
        "public": false
      },
      {
        "input": "-5 0 9",
        "expected": "-5",
        "public": false
      },
      {
        "input": "0 2",
        "expected": "0",
        "public": false
      }
    ]
  },
  {
    "id": "9",
    "title": "Секретный код инопланетян",
    "statement": "Инопланетяне прислали слово. Подсчитай количество символов в нём.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одно непустое слово из русских или латинских букв, длиной до 1000 символов.",
    "output_description": "Количество символов.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "Python",
        "expected": "6",
        "public": true
      },
      {
        "input": "звезда",
        "expected": "6",
        "public": false
      },
      {
        "input": "Я",
        "expected": "1",
        "public": false
      },
      {
        "input": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "expected": "1000",
        "public": false
      }
    ]
  },
  {
    "id": "10",
    "title": "Крик космического монстра",
    "statement": "Переведи имя космического монстра в заглавные буквы.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Непустое имя из русских или латинских букв, длиной до 1000 символов.",
    "output_description": "Имя в верхнем регистре.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "привет",
        "expected": "ПРИВЕТ",
        "public": true
      },
      {
        "input": "Python",
        "expected": "PYTHON",
        "public": false
      },
      {
        "input": "РОБИ",
        "expected": "РОБИ",
        "public": false
      },
      {
        "input": "я",
        "expected": "Я",
        "public": false
      }
    ]
  },
  {
    "id": "11",
    "title": "Приветствие от робота",
    "statement": "Напиши функцию greet(name), которая выводит приветствие «Привет, [имя]!». Затем считай имя и вызови функцию.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одно непустое имя без пробелов, до 100 символов.",
    "output_description": "Привет, [имя]!",
    "constraints": "Используй функцию greet(name). Наличие и использование функции проверяет преподаватель.",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "Иван",
        "expected": "Привет, Иван!",
        "public": true
      },
      {
        "input": "Анна",
        "expected": "Привет, Анна!",
        "public": false
      },
      {
        "input": "Robi",
        "expected": "Привет, Robi!",
        "public": false
      }
    ]
  },
  {
    "id": "12",
    "title": "Усиление сигнала звезды",
    "statement": "Напиши функцию double_signal(signal), которая возвращает число, умноженное на 2. Затем считай сигнал, вызови функцию и выведи результат.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одно целое число от −1000000 до 1000000.",
    "output_description": "Удвоенное число.",
    "constraints": "Используй функцию double_signal(signal). Наличие и использование функции проверяет преподаватель.",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "6",
        "expected": "12",
        "public": true
      },
      {
        "input": "0",
        "expected": "0",
        "public": false
      },
      {
        "input": "-7",
        "expected": "-14",
        "public": false
      },
      {
        "input": "1000000",
        "expected": "2000000",
        "public": false
      }
    ]
  },
  {
    "id": "13",
    "title": "Площадь звёздного щита",
    "statement": "Вычисли площадь квадратного щита: умножь длину стороны на саму себя.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Целая длина стороны от 1 до 1000000.",
    "output_description": "Площадь щита.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "4",
        "expected": "16",
        "public": true
      },
      {
        "input": "1",
        "expected": "1",
        "public": false
      },
      {
        "input": "9",
        "expected": "81",
        "public": false
      },
      {
        "input": "1000000",
        "expected": "1000000000000",
        "public": false
      }
    ]
  },
  {
    "id": "14",
    "title": "Загадка трёх планет",
    "statement": "Загадка Зефиры решается, если число делится на 3 без остатка. Проверь число.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Целое число от −1000000 до 1000000.",
    "output_description": "Делится / Не делится.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "9",
        "expected": "Делится",
        "public": true
      },
      {
        "input": "7",
        "expected": "Не делится",
        "public": true
      },
      {
        "input": "0",
        "expected": "Делится",
        "public": false
      },
      {
        "input": "-6",
        "expected": "Делится",
        "public": false
      },
      {
        "input": "-5",
        "expected": "Не делится",
        "public": false
      }
    ]
  },
  {
    "id": "16",
    "title": "Звёздная лотерея инопланетян",
    "statement": "Проверь, входит ли введённое число в лотерею с числами от 1 до 5 включительно.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одно целое число от −1000000 до 1000000.",
    "output_description": "Ура, это лотерейное число! / Это число не в лотерее.",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "3",
        "expected": "Ура, это лотерейное число!",
        "public": true
      },
      {
        "input": "6",
        "expected": "Это число не в лотерее.",
        "public": true
      },
      {
        "input": "1",
        "expected": "Ура, это лотерейное число!",
        "public": false
      },
      {
        "input": "5",
        "expected": "Ура, это лотерейное число!",
        "public": false
      },
      {
        "input": "0",
        "expected": "Это число не в лотерее.",
        "public": false
      },
      {
        "input": "-1",
        "expected": "Это число не в лотерее.",
        "public": false
      }
    ]
  },
  {
    "id": "17",
    "title": "Секретный пароль для базы",
    "statement": "Проверь, состоит ли пароль только из цифр. Пустой пароль не принимается.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одна строка длиной до 1000 символов из букв, цифр 0–9, пробелов и знаков пунктуации.",
    "output_description": "Пароль принят! / Пароль должен быть числом!",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "123",
        "expected": "Пароль принят!",
        "public": true
      },
      {
        "input": "abc",
        "expected": "Пароль должен быть числом!",
        "public": true
      },
      {
        "input": "001",
        "expected": "Пароль принят!",
        "public": false
      },
      {
        "input": "12a",
        "expected": "Пароль должен быть числом!",
        "public": false
      },
      {
        "input": "-1",
        "expected": "Пароль должен быть числом!",
        "public": false
      },
      {
        "input": "12 3",
        "expected": "Пароль должен быть числом!",
        "public": false
      },
      {
        "input": "",
        "expected": "Пароль должен быть числом!",
        "public": false
      }
    ]
  },
  {
    "id": "18",
    "title": "Кодовая фраза",
    "statement": "Проверь, состоит ли кодовая фраза только из букв. Пустая строка не принимается.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одна строка длиной до 1000 символов из русских и латинских букв, цифр, пробелов и знаков пунктуации.",
    "output_description": "Фраза принята! / Фраза должна быть из букв!",
    "constraints": "",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "привет",
        "expected": "Фраза принята!",
        "public": true
      },
      {
        "input": "123",
        "expected": "Фраза должна быть из букв!",
        "public": true
      },
      {
        "input": "Python",
        "expected": "Фраза принята!",
        "public": false
      },
      {
        "input": "Привет мир",
        "expected": "Фраза должна быть из букв!",
        "public": false
      },
      {
        "input": "abc1",
        "expected": "Фраза должна быть из букв!",
        "public": false
      },
      {
        "input": "!",
        "expected": "Фраза должна быть из букв!",
        "public": false
      },
      {
        "input": "",
        "expected": "Фраза должна быть из букв!",
        "public": false
      }
    ]
  },
  {
    "id": "19",
    "title": "Космический алтарь кристаллов",
    "statement": "Создай словарь: рубин — красный, изумруд — зелёный, сапфир — синий. Выведи цвет рубина.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Ввод не требуется.",
    "output_description": "красный",
    "constraints": "Используй словарь. Наличие словаря в коде проверяет преподаватель.",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "",
        "expected": "красный",
        "public": true
      }
    ]
  },
  {
    "id": "20",
    "title": "Секреты звёздного рейтинга",
    "statement": "Создай словарь рейтингов роботов: Роби — 10, Астро — 25, Луна — 15. Считай имя и выведи рейтинг или «Нет такого робота», если имени нет в словаре.\n\nСчитайте данные без текстовых приглашений и выведите только ответ.",
    "input_description": "Одно непустое имя без пробелов, до 100 символов. Регистр букв учитывается.",
    "output_description": "Рейтинг или Нет такого робота.",
    "constraints": "Используй словарь. Наличие словаря в коде проверяет преподаватель.",
    "difficulty": "easy",
    "points": 100,
    "time_limit": 2,
    "memory_limit": 128,
    "tests": [
      {
        "input": "Роби",
        "expected": "10",
        "public": true
      },
      {
        "input": "Бип",
        "expected": "Нет такого робота",
        "public": true
      },
      {
        "input": "Астро",
        "expected": "25",
        "public": false
      },
      {
        "input": "Луна",
        "expected": "15",
        "public": false
      },
      {
        "input": "роби",
        "expected": "Нет такого робота",
        "public": false
      }
    ]
  }
];
