import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import helmet from 'helmet';
import { AppModule } from './app.module.js';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.use(helmet());
  app.enableCors({
    origin: process.env.CORS_ORIGIN,
    credentials: true,
  });
  const config = new DocumentBuilder()
    .setTitle('HR Management API')
    .setDescription('Tài liệu API hệ thống Quản trị Nhân sự HRM')
    .setVersion('1.0')
    .addBearerAuth(
      {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        name: 'JWT',
        description: 'Nhập JWT access token vào đây',
        in: 'header',
      },
      'JWT-auth',
    )
    .build();

  const documentFactory = () => {
    const doc = SwaggerModule.createDocument(app, config, {
      operationIdFactory: (_controllerKey: string, methodKey: string) =>
        methodKey,
    });

    for (const [path, pathItem] of Object.entries(doc.paths)) {
      const rootPath = path.replace(/^\//, '').split('/')[0];
      if (rootPath) {
        const tagName = rootPath
          .split('-')
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
        for (const method of Object.values(pathItem)) {
          if (
            typeof method === 'object' &&
            method !== null &&
            (!('tags' in method) ||
              !method.tags ||
              method.tags.length === 0 ||
              method.tags.includes('default'))
          ) {
            (method as { tags?: string[] }).tags = [tagName];
          }
        }
      }
    }

    return doc;
  };

  SwaggerModule.setup('api/docs', app, documentFactory, {
    swaggerOptions: {
      persistAuthorization: true,
    },
  });

  await app.listen(process.env.PORT ?? 3000);
}
await bootstrap();
