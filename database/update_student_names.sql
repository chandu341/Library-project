USE library_management;

UPDATE users
SET name = 'Ratna',
    username = 'Ratna',
    email = 'jatlaratnakumari2@gmail.com',
    password_hash = 'scrypt:32768:8:1$jk6Q3fUqoNk4zead$5d4c2fdac93da25b9171a2ac9c20fd2b87e4d4da2d38bcdb874a41c64f75f7bd535e0b3a1da5278ae2c082de6cd68c72de1e2f7269fc33ed40804e00deca72d4'
WHERE username = 'Anu' OR name = 'Anu';

UPDATE users
SET name = 'Pannu',
    username = 'Pannu',
    email = 'pannu@gmail.com',
    password_hash = 'scrypt:32768:8:1$HFEiB3AYIT9Txf8l$5f75b4a2e2d7249024093b76f3c2efd08ab85ab80d3d2bfe355ec822b2982274215c9014a76fe065af588899dc0cf6327769f596e3942fdfac81f63ae80aeb0f'
WHERE username = 'Ravi' OR name = 'Ravi';

UPDATE users
SET name = 'Karuna',
    username = 'Karuna',
    email = 'karuna@gmail.com',
    password_hash = 'scrypt:32768:8:1$lilWYYJqVRaNSU1c$29de224bf31d62e49389163f3787560f5a14db1a0413767b2f5f2391a90eb9714f78067d218098320f6e903563999564041af8d43fe90006c18b2692c62e28ab'
WHERE username = 'Sneha' OR name = 'Sneha';

UPDATE users
SET name = 'Satya',
    username = 'Satya',
    email = 'satya@gmail.com',
    password_hash = 'scrypt:32768:8:1$d3DwSpQV3CpXNCsn$1378d68c5d8637f9a01e20cd85013bf4806a4e63d73b95acc0f4b753056f295f8c0e127f79447c9259d076128964c20b9d5b1f9a2a9d60891ef93875605d5fd4'
WHERE username = 'Kiran' OR name = 'Kiran';
