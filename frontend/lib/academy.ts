export const academyChapters = [
 {chapter:1,title:'Код от двери',stars:1,topic:'Числа и циклы',location:'Учебный корпус',description:'Разгадай код и выйди из заблокированного класса.'},
 {chapter:2,title:'Повреждённый пропуск',stars:2,topic:'Массивы',location:'Пункт доступа',description:'Восстанови запасной уровень доступа из архива.'},
 {chapter:3,title:'Сообщение Null',stars:2,topic:'Строки и два указателя',location:'Терминал связи',description:'Удали повреждённый символ и расшифруй сообщение.'},
 {chapter:4,title:'Энергетический тоннель',stars:3,topic:'Последовательности',location:'Энергоблок',description:'Найди самый длинный участок растущей энергии.'},
 {chapter:5,title:'Два ключа',stars:3,topic:'Словари и подсчёт пар',location:'Хранилище ключей',description:'Подсчитай пары ключей, открывающих следующую дверь.'},
 {chapter:6,title:'Лабиринт Академии',stars:4,topic:'Графы и BFS',location:'Закрытые коридоры',description:'Проложи кратчайший путь через уцелевшие проходы.'},
 {chapter:7,title:'Резервное питание',stars:4,topic:'Динамическое программирование',location:'Серверная',description:'Подбери батареи и восстанови питание без перегрузки.'},
 {chapter:8,title:'Последний протокол',stars:5,topic:'Графы и BFS',location:'Центральное ядро',description:'Пройди сеть телепортов и останови уничтожение системы.'},
];
export type AcademyTemplate = {chapter:number;stars:number;topic:string;title:string;statement:string;input_description:string;output_description:string;constraints:string;difficulty:string;points:number;time_limit:number;memory_limit:number;tests:{input:string;expected:string;public:boolean}[]};
