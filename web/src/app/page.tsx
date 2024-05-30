"use client";
import { Footer } from "@/app/components/footer";
import { PresetQuery } from "@/app/components/preset-query";
import { Search } from "@/app/components/search";
import React from "react";

export default function Home() {
	return (
		<div className="absolute inset-0 min-h-[500px] flex items-center justify-center">
			<div className="relative flex flex-col gap-8 px-4 -mt-24">
				<Search></Search>
				<div className="flex gap-2 flex-wrap justify-center">
					<PresetQuery query="I want to train an image classification model."></PresetQuery>
					<PresetQuery query="Help me extract the features from CSV data."></PresetQuery>
				</div>
				<Footer></Footer>
			</div>
		</div>
	);
}
