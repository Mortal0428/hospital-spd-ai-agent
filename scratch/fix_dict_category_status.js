const fs = require('fs');
const filePath = 'backend/app/routers/dict_router.py';
let content = fs.readFileSync(filePath, 'utf8');

const target = `            new_cat = SpdCategory(
                category_code=sc["category_code"],
                category_name=sc["category_name"],
                main_dept_code=sc["main_dept_code"],
                consumable_level=sc["consumable_level"],
                sort_order=sc["sort_order"],
                status=1
            )`;

const replacement = `            new_cat = SpdCategory(
                category_code=sc["category_code"],
                category_name=sc["category_name"],
                main_dept_code=sc["main_dept_code"],
                consumable_level=sc["consumable_level"],
                sort_order=sc["sort_order"]
            )`;

if (content.includes(target)) {
  content = content.replace(target, replacement);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log('Successfully fixed SpdCategory status=1 in dict_router.py');
} else {
  console.error('Target not found in dict_router.py');
}
