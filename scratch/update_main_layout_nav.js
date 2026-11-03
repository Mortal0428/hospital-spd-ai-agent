const fs = require('fs');
const filePath = 'frontend/src/layouts/MainLayout.vue';
let content = fs.readFileSync(filePath, 'utf8');

const target = `@click="navigateMenu('/users', 'list')"`;
const replacement = `@click="navigateMenu('/users', 'users')"`;

if (content.includes(target)) {
  content = content.replace(target, replacement);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('MainLayout.vue nav updated');
} else {
  console.log('target not found in MainLayout');
}
