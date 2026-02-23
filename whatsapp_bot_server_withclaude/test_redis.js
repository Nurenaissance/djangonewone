/**
 * Redis Connection Test Script
 * Run this to verify Redis connection works
 */
import { createClient } from 'redis';
import dotenv from 'dotenv';

dotenv.config();

async function testRedisConnection() {
  console.log('🧪 Testing Redis Connection...\n');

  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
  console.log('📋 Redis URL:', redisUrl.replace(/:[^:@]+@/, ':***@'));  // Hide password

  try {
    console.log('⏳ Connecting to Redis...');

    const client = createClient({
      url: redisUrl,
      socket: {
        connectTimeout: 10000,
        tls: redisUrl.startsWith('rediss://'),  // Enable TLS for rediss://
        rejectUnauthorized: false  // Accept self-signed certs (Azure uses valid certs)
      }
    });

    client.on('error', (err) => {
      console.error('❌ Redis Error:', err.message);
    });

    client.on('ready', () => {
      console.log('✅ Redis connected successfully!');
    });

    await client.connect();

    // Test SET operation
    console.log('\n⏳ Testing SET operation...');
    await client.set('test_key', 'test_value');
    console.log('✅ SET successful');

    // Test GET operation
    console.log('\n⏳ Testing GET operation...');
    const value = await client.get('test_key');
    console.log('✅ GET successful, value:', value);

    // Test DELETE operation
    console.log('\n⏳ Testing DELETE operation...');
    await client.del('test_key');
    console.log('✅ DELETE successful');

    // Get Redis info
    console.log('\n📊 Redis Server Info:');
    const info = await client.info();
    const lines = info.split('\n').slice(0, 5);
    lines.forEach(line => console.log(`   ${line}`));

    await client.quit();
    console.log('\n🎉 All tests passed! Redis connection is working correctly.');

  } catch (error) {
    console.error('\n❌ Redis connection failed:');
    console.error('Error:', error.message);

    if (error.code === 'ECONNREFUSED') {
      console.error('\n💡 Possible causes:');
      console.error('   1. Redis server is not running');
      console.error('   2. Wrong hostname or port');
      console.error('   3. Firewall blocking connection');
    } else if (error.code === 'ETIMEDOUT') {
      console.error('\n💡 Connection timeout - check:');
      console.error('   1. Network connectivity');
      console.error('   2. Azure Redis firewall rules');
      console.error('   3. DNS resolution for hostname');
    } else if (error.message.includes('auth')) {
      console.error('\n💡 Authentication failed - check:');
      console.error('   1. Redis password is correct');
      console.error('   2. Password format in URL is correct');
      console.error('   3. Access key not regenerated recently');
    }

    process.exit(1);
  }
}

// Run test
testRedisConnection();
