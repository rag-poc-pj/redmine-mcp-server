/**
 * AWS Lambda エントリーポイント
 * API Gateway + Lambda Proxy Integration
 */

import serverlessHttp from "serverless-http";
import app from "./app.js";

export const handler = serverlessHttp(app);
