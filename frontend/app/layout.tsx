import './globals.css';
import Nav from '@/components/Nav';
export const metadata={title:'Python Олимпиады — школьники и СПО',description:'Две независимые олимпиады по программированию на Python'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="ru"><body><Nav/>{children}<footer className="footer">Python Олимпиады · Школьники и СПО · Все даты указаны по Екатеринбургу (UTC+5)</footer></body></html>}
