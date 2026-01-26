BEGIN {
	src = "";
	dst = "";
	addressPair = "";
	protocol = "";

	lineCount = 0;
	srcStartIndex = 0;
	srcEndIndex = 0;
	dstStartIndex = 0;
	dstEndIndex = 0;
	uniquePairCount = 1;
	
	protocolCount["UDP"] = 0;
	protocolCount["TCP"] = 0;
	protocolCount["unknown"] = 0;
}

{
	# remove first 2 : in the timestamp
	sub(":", ".", $0);
	sub(":", ".", $0);

	# find src and dst
	srcStartIndex = index($0, "IP");
	if(srcStartIndex == 0)
		next;
	srcStartIndex += 3;
	dstEndIndex = index($0, ":") - 1;
	addressPair = substr($0, srcStartIndex, dstEndIndex - srcStartIndex + 1);

	if($0 ~ "UDP")
		protocol = "UDP";
	else if($0 ~ "Flags")
		protocol = "TCP";
	else
		protocol = "unknown";

	for(i = 0;i<uniquePairCount;i++)
	{
		if(pair[i] == addressPair && pairProtocol[i] == protocol)
		{
			pairCount[i]++;
			break;
		}
	}
	if(i == uniquePairCount)
	{
		pair[uniquePairCount] = addressPair;
		pairCount[uniquePairCount] = 1;
		pairProtocol[uniquePairCount] = protocol;
		uniquePairCount++;
	}

	protocolCount[protocol]++;
	lineCount++;
}

END {
	for(i = 0;i<uniquePairCount;i++)
		printf "%s : %d : %s\n", pair[i], pairCount[i], pairProtocol[i];

	printf "total packets:\t%d\nTCP:\t\t%d\nUDP:\t\t%d\nunknown:\t%d\n", lineCount, protocolCount["TCP"], protocolCount["UDP"], protocolCount["unknown"];
}
