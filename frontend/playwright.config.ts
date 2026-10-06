import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',workers:1,use:{baseURL:process.env.TEST_BASE_URL||'http://localhost:8080',headless:true,launchOptions:{executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']},screenshot:'only-on-failure'},reporter:'list'});
