import http from 'k6/http';
import { check } from 'k6';
import { Rate } from 'k6/metrics';

// A metric to track failure rates
export const errorRate = new Rate('errors');

// Options for the load test
export const options = {
  vus: 50,          // 50 virtual users
  duration: '10s',  // run for 10 seconds
  thresholds: {
    'http_req_failed': ['rate<0.01'], // <1% errors
    'http_req_duration': ['p(95)<200'], // 95% of requests must complete below 200ms
    'errors': ['rate<0.01'],
  },
};

const BASE_URL = 'http://localhost:8000/api/v1';

export default function () {
  const payload = JSON.stringify({
    // Generate a random name to avoid any potential caching
    player_name: `guest_${__VU}_${__ITER}`,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(`${BASE_URL}/auth_guest`, payload, params);

  // Check for successful response
  const success = check(res, {
    'status is 200': (r) => r.status === 200,
  });

  // Add to error rate if check fails
  if (!success) {
    errorRate.add(1);
  }
}
