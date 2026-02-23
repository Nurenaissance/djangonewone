import dotenv from 'dotenv';
dotenv.config();

console.log('OPENAI_API_KEY from env:', process.env.OPENAI_API_KEY?.substring(0, 20) + '...');
console.log('Full first part:', process.env.OPENAI_API_KEY?.substring(0, 10));
