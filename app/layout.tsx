import type { Metadata } from "next";
import { Days_One } from "next/font/google";
import "./globals.css";

const daysOne = Days_One({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-days-one",
});

export const metadata: Metadata = {
  title: "Kallipolis",
  description: "A new foundation for how institutions think and act",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={daysOne.variable}>
      <body>{children}</body>
    </html>
  );
}
