import './globals.css';
import Nav from '@/components/Nav';
export const metadata={title:'Сбой в Академии Алгоритмов — олимпиада по Python',description:'Восемь глав одного приключения. Восстанови работу Питонии и останови Null, решая задачи на Python.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="ru"><body><Nav/>{children}<footer className="footer">Академия Алгоритмов · Python · Школьники и СПО · Все даты указаны по Екатеринбургу (UTC+5)</footer></body></html>}
