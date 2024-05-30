import { FC } from "react";

export const Footer: FC = () => {
	return (
		<div className="text-center flex flex-col items-center text-xs text-zinc-700 gap-1">
			<div className="text-zinc-400">
				The project plan, script and analysis are generated by large language
				models, please use with caution.
			</div>
		</div>
	);
};