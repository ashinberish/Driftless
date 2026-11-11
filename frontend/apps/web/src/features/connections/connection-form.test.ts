import { describe, expect, it } from "vitest";

import { emptyForm, parseConnectionString, toCreate, validate } from "./connection-form";

const valid = {
  ...emptyForm(),
  name: "billing-prod",
  host: "db.internal",
  database: "billing",
  username: "ro",
  secretRef: "vault:db/billing-ro",
};

describe("validate", () => {
  it("accepts a complete form", () => {
    expect(validate(valid)).toEqual({});
  });

  it("rejects a plaintext password in the secret field", () => {
    expect(validate({ ...valid, secretRef: "hunter2" }).secretRef).toMatch(/never the password/);
  });

  it("checks port range and required fields", () => {
    const errors = validate({ ...valid, host: " ", port: "70000", name: "" });
    expect(Object.keys(errors).sort()).toEqual(["host", "name", "port"]);
  });

  it("can skip the name when only testing", () => {
    expect(validate({ ...valid, name: "" }, { requireName: false })).toEqual({});
  });
});

describe("parseConnectionString", () => {
  it("fills fields from a postgres URL and drops the password", () => {
    const parsed = parseConnectionString(
      "postgresql://driftless_ro:s3cret@billing-01.corp:6432/billing?sslmode=require",
    );
    expect(parsed?.values).toEqual({
      engine: "postgres",
      host: "billing-01.corp",
      port: "6432",
      database: "billing",
      username: "driftless_ro",
      sslMode: "require",
    });
    expect(parsed?.droppedPassword).toBe(true);
  });

  it("uses the engine's default port", () => {
    expect(parseConnectionString("mysql://app@db/shop")?.values.port).toBe("3306");
  });

  it("returns null for unknown schemes or garbage", () => {
    expect(parseConnectionString("redis://x")).toBeNull();
    expect(parseConnectionString("not a url")).toBeNull();
  });
});

describe("toCreate", () => {
  it("trims values and converts the port", () => {
    expect(toCreate({ ...valid, host: " db.internal ", port: "5433" })).toMatchObject({
      host: "db.internal",
      port: 5433,
      secret_ref: "vault:db/billing-ro",
      ssl_mode: "prefer",
    });
  });
});
